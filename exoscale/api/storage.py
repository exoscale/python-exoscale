# -*- coding: utf-8 -*-

"""
This submodule represents the Exoscale Storage API.
"""

import attr
import boto3
import botocore
from . import API, Resource, APIException, ResourceNotFoundError
from os.path import basename
from urllib.parse import urljoin

_DEFAULT_ZONE = "ch-gva-2"

_SUPPORTED_CANNED_ACLS = {
    "private",
    "public-read",
    "public-read-write",
    "authenticated-read",
    "bucket-owner-read",
    "bucket-owner-full-control",
}

ACL_ALL_USERS = "http://acs.amazonaws.com/groups/global/AllUsers"
ACL_AUTHENTICATED_USERS = "http://acs.amazonaws.com/groups/global/AuthenticatedUsers"


@attr.s
class CORSRule(Resource):
    """
    A Storage bucket CORS rule.

    Attributes:
        allowed_headers ([str]): list of allowed HTTP headers
        allowed_methods ([str]): list of allowed HTTP methods
        allowed_origins ([str]): list of allowed HTTP origins
        expose_headers ([str]): list of HTTP headers allowed to be exposed in response
        max_age_seconds (int): time in seconds that a browser can cache OPTIONS reponse
    """

    res = attr.ib(repr=False)
    allowed_headers = attr.ib(default=None, repr=False)
    allowed_methods = attr.ib(default=None, repr=False)
    allowed_origins = attr.ib(default=None, repr=False)
    expose_headers = attr.ib(default=None, repr=False)
    max_age_seconds = attr.ib(default=None, repr=False)

    @classmethod
    def from_s3(cls, res):
        return cls(
            res,
            allowed_headers=res["AllowedHeaders"],
            allowed_methods=res["AllowedMethods"],
            allowed_origins=res["AllowedOrigins"],
            expose_headers=res.get("ExposeHeaders", None),
            max_age_seconds=res.get("MaxAgeSeconds", None),
        )

    def to_s3(self):
        """
        Serialize a CORSRule class instance to the AWS S3 CORS rule format.

        References:
            * `AWS S3 CORS rule format`_

            .. _AWS S3 CORS rule format: https://docs.aws.amazon.com/AmazonS3/latest/API/RESTBucketPUTcors.html
        """

        cors_rule = {
            "AllowedHeaders": getattr(self, "allowed_headers", []),
            "AllowedMethods": getattr(self, "allowed_methods", []),
            "AllowedOrigins": getattr(self, "allowed_origins", []),
        }

        if self.expose_headers is not None:
            cors_rule["ExposeHeaders"] = self.expose_headers

        if self.max_age_seconds is not None:
            cors_rule["MaxAgeSeconds"] = self.max_age_seconds

        return cors_rule


@attr.s
class AccessControlPolicy(Resource):
    """
    A Storage Access Control Policy.

    Attributes:
        owner (str): entity owner of the resource
        full_control (str): full control grant
        read (str): read permission grant
        write (str): write permission grant
        read_acp (str): Access Control Policy read permission grant
        write_acp (str): Access Control Policy write permission grant
    """

    res = attr.ib(repr=False)
    owner = attr.ib()
    full_control = attr.ib(default=None, repr=False)
    read = attr.ib(default=None, repr=False)
    write = attr.ib(default=None, repr=False)
    read_acp = attr.ib(default=None, repr=False)
    write_acp = attr.ib(default=None, repr=False)

    @classmethod
    def from_s3(cls, res):
        acp = cls(res, owner=res["Owner"]["ID"])

        for i in res["Grants"]:
            if i["Permission"] == "FULL_CONTROL":
                acp.full_control = acp._grantee_from_s3(i["Grantee"])
            if i["Permission"] == "READ":
                acp.read = acp._grantee_from_s3(i["Grantee"])
            if i["Permission"] == "WRITE":
                acp.write = acp._grantee_from_s3(i["Grantee"])
            if i["Permission"] == "READ_ACP":
                acp.read_acp = acp._grantee_from_s3(i["Grantee"])
            if i["Permission"] == "WRITE_ACP":
                acp.write_acp = acp._grantee_from_s3(i["Grantee"])

        return acp

    def to_s3(self):
        """
        Serialize an AccessControlPolicy class instance to the AWS S3 Access Control
        Policy format.

        References:
            * `boto3 AccessControlPolicy format`_

            .. _boto3 AccessControlPolicy format: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.put_bucket_acl
        """

        acp = {"Owner": {"ID": self.owner, "DisplayName": self.owner}, "Grants": []}

        if self.full_control is not None:
            acp["Grants"].append(
                {
                    "Grantee": self._grantee_to_s3(self.full_control),
                    "Permission": "FULL_CONTROL",
                }
            )
        if self.read is not None:
            acp["Grants"].append(
                {"Grantee": self._grantee_to_s3(self.read), "Permission": "READ"}
            )
        if self.write is not None:
            acp["Grants"].append(
                {"Grantee": self._grantee_to_s3(self.write), "Permission": "WRITE"}
            )
        if self.read_acp is not None:
            acp["Grants"].append(
                {
                    "Grantee": self._grantee_to_s3(self.read_acp),
                    "Permission": "READ_ACP",
                }
            )
        if self.write_acp is not None:
            acp["Grants"].append(
                {
                    "Grantee": self._grantee_to_s3(self.write_acp),
                    "Permission": "WRITE_ACP",
                }
            )

        return acp

    def _grantee_from_s3(self, grantee):
        """
        Convert an AWS S3 Access Control Policy grantee to AccessControlPolicy class
        format.
        """

        if grantee["Type"] == "CanonicalUser":
            return grantee["ID"]
        else:
            if grantee["URI"] == ACL_ALL_USERS:
                return "ALL_USERS"
            elif grantee["URI"] == ACL_AUTHENTICATED_USERS:
                return "AUTHENTICATED_USERS"

        raise ValueError("unsupported grantee: {}".format(grantee))

    def _grantee_to_s3(self, grantee):
        """
        Convert an AccessControlPolicy class to AWS S3 Access Control Policy grantee 
        format.

        References:
            * `boto3 AccessControlPolicy format`_

            .. _boto3 AccessControlPolicy format: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.put_bucket_acl
        """

        if grantee in {"ALL_USERS", "AUTHENTICATED_USERS"}:
            if grantee == "ALL_USERS":
                uri = ACL_ALL_USERS
            else:
                uri = ACL_AUTHENTICATED_USERS
            return {"Type": "Group", "URI": uri}
        else:
            return {"Type": "CanonicalUser", "ID": grantee, "DisplayName": grantee}


@attr.s
class BucketFile(Resource):
    """
    A file stored in Storage bucket.

    Attributes:
        path (str): the stored file path
        bucket (Bucket): the bucket the file is stored into
    """

    storage = attr.ib(repr=False)
    res = attr.ib(repr=False)
    path = attr.ib()
    bucket = attr.ib(repr=False)

    @property
    def content(self):
        """
        Stored file content.

        Returns:
            botocore.response.StreamingBody: the stored file content body

        Example:
            To read the content of a stored file::

                for f in mybucket.list_files():
                    print(f.content.read())

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.

        References:
            * `botocore.response API`_

            .. _botocore.response API: https://botocore.amazonaws.com/v1/documentation/api/latest/reference/response.html
        """

        try:
            res = self.storage.boto.get_object(Bucket=self.bucket.name, Key=self.path)
        except Exception as e:
            raise APIException(e)

        return res["Body"]

    @property
    def size(self):
        """
        Stored file size.

        Returns:
            int: the stored file size in bytes

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        if "Size" in self.res:
            return self.res["Size"]

        try:
            res = self.storage.boto.get_object(Bucket=self.bucket.name, Key=self.path)
        except Exception as e:
            raise APIException(e)

        return res["ContentLength"]

    @property
    def last_modification_date(self):
        """
        Stored file last modification date.

        Returns:
            datetime.datetime: the stored file last modification date

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.

        References:
            * `Python datetime module`_

            .. _Python datetime module: https://docs.python.org/3/library/datetime.html
        """

        if "LastModified" in self.res:
            return self.res["LastModified"]

        try:
            res = self.storage.boto.get_object(Bucket=self.bucket.name, Key=self.path)
        except Exception as e:
            raise APIException(e)

        return res["LastModified"]

    @property
    def acl(self):
        """
        Stored file Access Control List.

        Returns:
            AccessControlPolicy: the Access Control Policy applied to the stored file

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            res = self.storage.boto.get_object_acl(
                Bucket=self.bucket.name, Key=self.path
            )
        except Exception as e:
            raise APIException(e)

        res.pop("ResponseMetadata")
        return AccessControlPolicy.from_s3(res)

    @property
    def metadata(self):
        """
        Stored file metadata.

        Returns:
            dict: the stored file metadata

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            res = self.storage.boto.get_object(Bucket=self.bucket.name, Key=self.path)
        except Exception as e:
            raise APIException(e)

        return res["Metadata"]

    @property
    def url(self):
        """
        Stored file URL.

        Returns:
            str: the stored file URL

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        return urljoin(self.bucket.url, self.path)

    def set_acl(self, acl="", acp=None):
        """
        Set the stored file Access Control List.

        Parameters:
            acl (str): a canned ACL
            acp (AccessControlPolicy): an Access Control Policy

        Returns:
            None
        """

        if acl is None and acp is None:
            raise ValueError("either acl or acp must be specified")

        if acl != "" and acl not in _SUPPORTED_CANNED_ACLS:
            raise ValueError(
                "unsupported ACL; supported ACLs are: {}".format(
                    ",".join(_SUPPORTED_CANNED_ACLS)
                )
            )

        try:
            if acl != "":
                res = self.storage.boto.put_object_acl(
                    Bucket=self.bucket.name, Key=self.path, ACL=acl
                )
            else:
                res = self.storage.boto.put_object_acl(
                    Bucket=self.bucket.name,
                    Key=self.path,
                    AccessControlPolicy=acp.to_s3(),
                )
        except Exception as e:
            raise APIException(e)

    def delete(self):
        """
        Delete the stored file.

        Returns:
            None
        """

        try:
            res = self.storage.boto.delete_object(
                Bucket=self.bucket.name, Key=self.path
            )
        except Exception as e:
            raise APIException(e)

        self.storage = None
        self.res = None
        self.path = None
        self.bucket = None


@attr.s
class Bucket(Resource):
    """
    A Storage bucket.

    Attributes:
        name (str): the Storage bucket name
    """

    storage = attr.ib(repr=False)
    res = attr.ib(repr=False)
    name = attr.ib()

    @property
    def acl(self):
        """
        Storage bucket Access Control List.

        Returns:
            AccessControlPolicy: the Access Control Policy applied to the Storage bucket

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            res = self.storage.boto.get_bucket_acl(Bucket=self.name)
        except Exception as e:
            raise APIException(e)

        res.pop("ResponseMetadata")
        return AccessControlPolicy.from_s3(res)

    @property
    def cors(self):
        """
        Storage bucket Cross-Origin Resource Sharing configuration.

        Yields:
            CORSRule: the next CORS rule

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            res = self.storage.boto.get_bucket_cors(Bucket=self.name)
            for i in res["CORSRules"]:
                yield CORSRule.from_s3(i)
        except Exception as e:
            raise APIException(e)

    @property
    def zone(self):
        """
        Storage bucket zone.

        Returns:
            str: the Storage bucket zone

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            res = self.storage.boto.get_bucket_location(Bucket=self.name)
        except Exception as e:
            raise APIException(e)

        return res["LocationConstraint"]

    @property
    def url(self):
        """
        URL of the Storage bucket.

        Returns:
            str: the Storage bucket URL

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        return "https://sos-{zone}.exo.io/{bucket}".format(
            zone=self.zone, bucket=self.name
        )

    def put_file(self, src, dst=None, metadata=None, acl=None, transferConfig=None):
        """
        Store a file in the bucket.

        Parameters:
            src (str): the path to the source file
            dst (str): a path to which to store the file in the bucket 
            metadata (dict): a dict of metadata to set to the file
            acl (str): a canned ACL to apply to the file
            transferConfig (boto3.s3.transfer.TransferConfig): a boto3 transfer
                configuration

        Returns:
            BucketFile: the file stored in the bucket
        """

        if dst is None:
            dst = basename(src)

        extraArgs = {}
        if metadata:
            extraArgs["Metadata"] = metadata
        if acl is not None:
            if acl not in _SUPPORTED_CANNED_ACLS:
                raise ValueError(
                    "unsupported ACL; supported ACLs are: {}".format(
                        ",".join(_SUPPORTED_CANNED_ACLS)
                    )
                )
            extraArgs["ACL"] = acl

        try:
            self.storage.boto.upload_file(
                Filename=src,
                Bucket=self.name,
                Key=dst,
                ExtraArgs=extraArgs if len(extraArgs) > 0 else None,
                Config=transferConfig,
            )
        except Exception as e:
            raise APIException(e)

        return BucketFile(self.storage, {}, path=dst, bucket=self)

    def list_files(self, prefix=""):
        """
        List files stored in the bucket.

        Parameters:
            prefix (str): a path prefix to restrict results to

        Yields:
            BucketFile: the next file stored in the bucket
        """

        try:
            paginator = self.storage.boto.get_paginator("list_objects_v2")
            pages = paginator.paginate(
                Bucket=self.name, Prefix=prefix, PaginationConfig={"PageSize": 100}
            )
            for page in pages:
                for i in page["Contents"]:
                    yield BucketFile(self.storage, i, i["Key"], self)
        except Exception as e:
            raise APIException(e)

    def get_file(self, path):
        """
        Get a file stored in the bucket.

        Parameters:
            path (str): the path to the file stored in the bucket

        Returns:
            BucketFile: file stored in the bucket
        """

        try:
            res = self.storage.boto.get_object(Bucket=self.name, Key=path)
        except Exception as e:
            raise APIException(e)

        res.pop("ResponseMetadata")
        return BucketFile(self.storage, res, path=path, bucket=self)

    def delete_files(self, prefix=""):
        """
        Delete files stored in the bucket.

        Parameters:
            prefix (str): a path prefix to restrict files deletion to

        Returns:
            None
        """

        _MAX_DELETE_BATCH = 1000

        batches = []
        batch = []
        n = 0
        # Iterate over the list of files to delete, and pack batches of
        # _MAX_DELETE_BATCH files to be executed once we've finished listing
        for f in self.list_files(prefix):
            batch.append({"Key": f.path})
            n = n + 1

            # We reached maximum batch capacity, queue it and move on to the rest of
            # the list
            if n >= _MAX_DELETE_BATCH:
                batches.append(batch)
                batch = []
                n = 0

        # Include the remaining non-batched files
        if len(batch) > 0:
            batches.append(batch)

        # Perform objects batch deletions
        try:
            for ob in batches:
                res = self.storage.boto.delete_objects(
                    Bucket=self.name, Delete={"Objects": ob}
                )
        except Exception as e:
            raise APIException(e)

    def set_acl(self, acl="", acp=None):
        """
        Set the Storage bucket Access Control List.

        Parameters:
            acl (str): a canned ACL
            acp (AccessControlPolicy): an Access Control Policy

        Returns:
            None
        """

        if acl is None and acp is None:
            raise ValueError("either acl or acp must be specified")

        if acl != "" and acl not in _SUPPORTED_CANNED_ACLS:
            raise ValueError(
                "unsupported ACL; supported ACLs are: {}".format(
                    ",".join(_SUPPORTED_CANNED_ACLS)
                )
            )

        try:
            if acl != "":
                res = self.storage.boto.put_bucket_acl(Bucket=self.name, ACL=acl)
            else:
                res = self.storage.boto.put_bucket_acl(
                    Bucket=self.name, AccessControlPolicy=acp.to_s3()
                )
        except Exception as e:
            raise APIException(e)

    def set_cors(self, rules):
        """
        Set the Storage bucket Cross-Origin Resource Sharing configuration.

        Parameters:
            rules ([CORSRule]): a list of CORS rules

        Returns:
            None
        """

        try:
            res = self.storage.boto.put_bucket_cors(
                Bucket=self.name,
                CORSConfiguration={"CORSRules": list(r.to_s3() for r in rules)},
            )
        except Exception as e:
            raise APIException(e)

    def delete(self):
        """
        Delete the Storage bucket.

        Returns:
            None
        """

        try:
            res = self.storage.boto.delete_bucket(Bucket=self.name)
        except Exception as e:
            raise APIException(e)

        self.storage = None
        self.res = None
        self.name = None


class StorageAPI(API):
    """
    An Exoscale Object Storage API client.

    Parameters:
        key (str): the Storage API key
        secret (str): the Storage API secret
        endpoint (str): the Storage API endpoint
        zone (str): the Storage zone
        trace (bool): API request/response tracing flag
    """

    def __init__(self, key, secret, endpoint=None, zone=None):
        self.zone = _DEFAULT_ZONE if zone is None else zone
        endpoint = (
            "https://sos-{}.exo.io".format(self.zone) if endpoint is None else endpoint
        )
        super().__init__(endpoint, key, secret)

        if self.zone is None:
            raise ValueError("no storage zone specified")

        self.boto = boto3.client(
            "s3",
            region_name=self.zone,
            endpoint_url=self.endpoint,
            aws_access_key_id=key,
            aws_secret_access_key=secret,
            config=botocore.client.Config(retries=dict(max_attempts=1)),
        )

    def __repr__(self):
        return "StorageAPI(endpoint='{}' zone='{}' key='{}')".format(
            self.endpoint, self.zone, self.key
        )

    def __str__(self):
        return self.__repr__()

    def create_bucket(self, name, zone=None, acl="private"):
        """
        Create a Storage bucket.

        Parameters:
            name (str): the Storage bucket name
            zone (str): a Storage bucket zone
            acl (str): a canned ACL to apply to the bucket

        Returns:
            Bucket: the Storage bucket created
        """

        if acl not in _SUPPORTED_CANNED_ACLS:
            raise ValueError(
                "unsupported ACL; supported ACLs are: {}".format(
                    ",".join(_SUPPORTED_CANNED_ACLS)
                )
            )

        try:
            res = self.boto.create_bucket(
                Bucket=name,
                CreateBucketConfiguration={
                    "LocationConstraint": self.zone if zone is None else zone
                },
                ACL=acl,
            )
        except Exception as e:
            raise APIException(e)

        return Bucket(self, {}, name=name)

    def list_buckets(self):
        """
        List Storage buckets.

        Yields:
            Bucket: the next Storage bucket
        """

        try:
            res = self.boto.list_buckets()
        except Exception as e:
            raise APIException(e)

        if "Buckets" in res:
            for bucket in res["Buckets"]:
                yield Bucket(self, bucket, name=bucket["Name"])

    def get_bucket(self, name):
        """
        Get a Storage bucket.

        Parameters:
            name (str): a Storage bucket name

        Returns:
            Bucket: a Storage bucket
        """

        for bucket in self.list_buckets():
            if bucket.name == name:
                return bucket

        raise ResourceNotFoundError
