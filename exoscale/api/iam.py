# -*- coding: utf-8 -*-

"""
This submodule represents the Exoscale IAM API.
"""

import attr
from . import API, Resource, APIException, ResourceNotFoundError
from cs import CloudStack, CloudStackApiException


@attr.s
class APIKey(Resource):
    """
    An API key.

    Attributes:
        name (str): the API key display name
        key (str): the API key unique identifier
        type (str): the API key type
        secret (str): the API key secret
        operations ([str]): a list of allowed API operations
    """

    iam = attr.ib(repr=False)
    res = attr.ib(repr=False)
    name = attr.ib()
    key = attr.ib()
    type = attr.ib()
    secret = attr.ib(repr=False)
    operations = attr.ib(repr=False)

    @classmethod
    def _from_cs(cls, iam, res):
        return cls(
            iam,
            res,
            name=res["name"],
            key=res["key"],
            type=res["type"],
            secret=res.get("secret", None),
            operations=res.get("operations", None),
        )

    def revoke(self):
        """
        Revoke the API key.

        Returns:
            None
        """

        try:
            self.iam.cs.revokeApiKey(key=self.key)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.res = None
        self.name = None
        self.key = None
        self.secret = None
        self.operations = None
        self.type = None


class IamAPI(API):
    """
    An Exoscale IAM API client.

    Parameters:
        key (str): the API key unique identifier
        secret (str): the IAM API secret
        endpoint (str): the IAM API endpoint
        max_retries (int): the API HTTP session retry policy number of retries to allow
        trace (bool): API request/response tracing flag
    """

    def __init__(
        self,
        key,
        secret,
        endpoint="https://api.exoscale.com/compute",
        max_retries=None,
        trace=False,
    ):
        super().__init__(
            endpoint=endpoint,
            key=key,
            secret=secret,
            max_retries=max_retries,
            trace=trace,
        )

        self.cs = CloudStack(
            key=key,
            secret=secret,
            endpoint=endpoint,
            session=self.session,
            headers={**self.session.headers, **{"User-Agent": self.user_agent}},
            trace=self.trace,
            fetch_result=True,
        )

    def __repr__(self):
        return "IamAPI(endpoint='{}' key='{}')".format(self.endpoint, self.key)

    def __str__(self):
        return self.__repr__()

    ### API key

    def create_api_key(self, name, operations=None):
        """
        Create an API key.

        Parameters:
            name (str): the API key name
            operations (str): a comma-separated list of allowed API operations

        Returns:
           APIKey: the API key created
        """

        try:
            res = self.cs.createApiKey(name=name, operations=operations)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return APIKey._from_cs(self, res["apikey"])

    def list_api_keys(self, **kwargs):
        """
        List API keys.

        Yields:
           APIKey: the next API key
        """

        try:
            _list = self.cs.listApiKeys(fetch_list=True, **kwargs)

            for i in _list:
                yield APIKey._from_cs(self, i)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def get_api_key(self, key):
        """
        Get an API key.

        Parameters:
            key (str): the API key unique identifier 

        Returns:
            APIKey: an API key
        """

        try:
            res = self.cs.getApiKey(key=key)
        except CloudStackApiException as e:
            if "The key is not found." in e.error["errortext"]:
                raise ResourceNotFoundError
            else:
                raise CloudStackApiException(e.error["errortext"], e.error)

        return APIKey._from_cs(self, res)

    def list_api_key_operations(self):
        """
        list all supported operations of an API key.

       Returns:
            [str]: list of operations for the current API key
        """

        try:
            res = self.cs.listApiKeyOperations()
        except CloudStackApiException as e:
            if "does not exist" in e.error["errortext"]:
                raise ResourceNotFoundError
            else:
                raise APIException(e.error["errortext"], e.error)

        return res["operations"]
