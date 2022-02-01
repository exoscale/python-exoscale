#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from .conftest import _random_str
from datetime import datetime
from exoscale.api.storage import AccessControlPolicy, Bucket, BucketFile


class TestStorageBucketFile:
    def test_set_acl(self, exo):
        bucket = Bucket(exo.storage, {}, _random_str())
        bucket_file = BucketFile(
            exo.storage, {}, path=_random_str(), bucket=bucket
        )

        bucket_file_acl = "public-read"
        bucket_file_acp = AccessControlPolicy(
            {},
            read=_random_str(),
            write=_random_str(),
            read_acp=_random_str(),
            write_acp=_random_str(),
            full_control=_random_str(),
            owner=_random_str(),
        )

        with pytest.raises(ValueError) as excinfo:
            bucket_file.set_acl()
        assert excinfo.type == ValueError

        with pytest.raises(ValueError) as excinfo:
            bucket_file.set_acl(acl="lolnope")
        assert excinfo.type == ValueError

        exo.boto_stub.add_response(
            "put_object_acl",
            {},
            {
                "Bucket": bucket.name,
                "Key": bucket_file.path,
                "ACL": bucket_file_acl,
            },
        )
        bucket_file.set_acl(acl=bucket_file_acl)

        exo.boto_stub.add_response(
            "put_object_acl",
            {},
            {
                "Bucket": bucket.name,
                "Key": bucket_file.path,
                "AccessControlPolicy": {
                    "Grants": [
                        {
                            "Grantee": {
                                "DisplayName": bucket_file_acp.full_control,
                                "ID": bucket_file_acp.full_control,
                                "Type": "CanonicalUser",
                            },
                            "Permission": "FULL_CONTROL",
                        },
                        {
                            "Grantee": {
                                "DisplayName": bucket_file_acp.read,
                                "ID": bucket_file_acp.read,
                                "Type": "CanonicalUser",
                            },
                            "Permission": "READ",
                        },
                        {
                            "Grantee": {
                                "DisplayName": bucket_file_acp.write,
                                "ID": bucket_file_acp.write,
                                "Type": "CanonicalUser",
                            },
                            "Permission": "WRITE",
                        },
                        {
                            "Grantee": {
                                "DisplayName": bucket_file_acp.read_acp,
                                "ID": bucket_file_acp.read_acp,
                                "Type": "CanonicalUser",
                            },
                            "Permission": "READ_ACP",
                        },
                        {
                            "Grantee": {
                                "DisplayName": bucket_file_acp.write_acp,
                                "ID": bucket_file_acp.write_acp,
                                "Type": "CanonicalUser",
                            },
                            "Permission": "WRITE_ACP",
                        },
                    ],
                    "Owner": {
                        "DisplayName": bucket_file_acp.owner,
                        "ID": bucket_file_acp.owner,
                    },
                },
            },
        )

        bucket_file.set_acl(acp=bucket_file_acp)

    def test_delete(self, exo):
        bucket = Bucket(exo.storage, {}, _random_str())
        bucket_file = BucketFile(
            exo.storage, {}, path=_random_str(), bucket=bucket
        )

        exo.boto_stub.add_response(
            "delete_object",
            {},
            {"Bucket": bucket.name, "Key": bucket_file.path},
        )

        bucket_file.delete()
        assert bucket_file.path is None

    def test_properties(self, exo, tmp_path):
        now = datetime.now()
        bucket_zone = "ch-gva-2"
        bucket = Bucket(exo.storage, {}, _random_str())
        bucket_file = BucketFile(
            exo.storage,
            {"LastModified": now},
            path=_random_str(),
            bucket=bucket,
        )

        file = tmp_path / _random_str()
        file.write_text(_random_str())

        assert bucket_file.last_modification_date == now

        exo.boto_stub.add_response(
            "get_object",
            {"ContentLength": len(file.read_text())},
            {"Bucket": bucket.name, "Key": bucket_file.path},
        )
        assert bucket_file.size == len(file.read_text())

        bucket_file_metadata = {"k": "v"}
        exo.boto_stub.add_response(
            "get_object",
            {"Metadata": bucket_file_metadata},
            {"Bucket": bucket.name, "Key": bucket_file.path},
        )
        assert bucket_file.metadata == bucket_file_metadata

        with open(file) as f:
            exo.boto_stub.add_response(
                "get_object",
                {"Body": f},
                {"Bucket": bucket.name, "Key": bucket_file.path},
            )
            assert bucket_file.content == f

        exo.boto_stub.add_response(
            "get_bucket_location",
            {"LocationConstraint": bucket_zone},
            {"Bucket": bucket.name},
        )
        assert bucket_file.url == "https://sos-{}.exo.io/{}/{}".format(
            bucket_zone, bucket.name, bucket_file.path
        )

        expected_acp = AccessControlPolicy(
            {},
            read=_random_str(),
            write=_random_str(),
            read_acp=_random_str(),
            write_acp=_random_str(),
            full_control=_random_str(),
            owner=_random_str(),
        )
        exo.boto_stub.add_response(
            "get_object_acl",
            {
                "Grants": [
                    {
                        "Grantee": {
                            "DisplayName": expected_acp.full_control,
                            "ID": expected_acp.full_control,
                            "Type": "CanonicalUser",
                        },
                        "Permission": "FULL_CONTROL",
                    },
                    {
                        "Grantee": {
                            "DisplayName": expected_acp.read,
                            "ID": expected_acp.read,
                            "Type": "CanonicalUser",
                        },
                        "Permission": "READ",
                    },
                    {
                        "Grantee": {
                            "DisplayName": expected_acp.write,
                            "ID": expected_acp.write,
                            "Type": "CanonicalUser",
                        },
                        "Permission": "WRITE",
                    },
                    {
                        "Grantee": {
                            "DisplayName": expected_acp.read_acp,
                            "ID": expected_acp.read_acp,
                            "Type": "CanonicalUser",
                        },
                        "Permission": "READ_ACP",
                    },
                    {
                        "Grantee": {
                            "DisplayName": expected_acp.write_acp,
                            "ID": expected_acp.write_acp,
                            "Type": "CanonicalUser",
                        },
                        "Permission": "WRITE_ACP",
                    },
                ],
                "Owner": {
                    "DisplayName": expected_acp.owner,
                    "ID": expected_acp.owner,
                },
                "ResponseMetadata": {},
            },
            {"Bucket": bucket.name, "Key": bucket_file.path},
        )
        actual_acp = bucket_file.acl
        assert actual_acp.full_control == expected_acp.full_control
        assert actual_acp.read == expected_acp.read
        assert actual_acp.write == expected_acp.write
        assert actual_acp.read_acp == expected_acp.read_acp
        assert actual_acp.write_acp == expected_acp.write_acp
