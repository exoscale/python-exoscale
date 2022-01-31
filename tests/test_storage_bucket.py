#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from .conftest import _random_str
from exoscale.api.storage import AccessControlPolicy, Bucket, CORSRule
from botocore.stub import ANY


class TestStorageBucket:
    def test_put_file(self, exo, tmp_path):
        bucket = Bucket(exo.storage, {}, _random_str())
        file_path = _random_str()
        file_metadata = {"k": "v"}

        file = tmp_path / file_path
        file.write_text(_random_str())

        exo.boto_stub.add_response(
            "put_object",
            {},
            {
                "Bucket": bucket.name,
                "Key": file_path,
                "Body": ANY,
                "Metadata": file_metadata,
            },
        )

        actual = bucket.put_file(str(file), metadata=file_metadata)
        assert actual.bucket == bucket
        assert actual.path == file_path

    def test_list_files(self, exo):
        bucket = Bucket(exo.storage, {}, _random_str())

        exo.boto_stub.add_response(
            "list_objects_v2",
            {"Contents": [{"Key": "test/file"}]},
            {"Bucket": bucket.name, "Prefix": "test/", "MaxKeys": ANY},
        )

        actual = list(bucket.list_files(prefix="test/"))
        assert len(actual) == 1
        assert actual[0].path == "test/file"

    def test_get_file(self, exo):
        bucket = Bucket(exo.storage, {}, _random_str())
        file_path = _random_str()

        exo.boto_stub.add_response(
            "get_object",
            {"ResponseMetadata": {}},
            {"Bucket": bucket.name, "Key": file_path},
        )

        file = bucket.get_file(file_path)
        assert file.bucket == bucket
        assert file.path == file_path

    def test_delete_files(self, exo):
        bucket = Bucket(exo.storage, {}, _random_str())
        file_path = _random_str()

        exo.boto_stub.add_response(
            "list_objects_v2",
            {"Contents": [{"Key": file_path}]},
            {"Bucket": bucket.name, "Prefix": file_path, "MaxKeys": ANY},
        )

        exo.boto_stub.add_response(
            "delete_objects",
            {},
            {
                "Bucket": bucket.name,
                "Delete": {"Objects": [{"Key": file_path}]},
            },
        )

        bucket.delete_files(prefix=file_path)

    def test_set_acl(self, exo):
        bucket = Bucket(exo.storage, {}, _random_str())
        bucket_acl = "public-read"
        bucket_acp = AccessControlPolicy(
            {},
            read=_random_str(),
            write=_random_str(),
            read_acp=_random_str(),
            write_acp=_random_str(),
            full_control=_random_str(),
            owner=_random_str(),
        )

        with pytest.raises(ValueError) as excinfo:
            bucket.set_acl()
        assert excinfo.type == ValueError

        with pytest.raises(ValueError) as excinfo:
            bucket.set_acl(acl="lolnope")
        assert excinfo.type == ValueError

        exo.boto_stub.add_response(
            "put_bucket_acl",
            {},
            {"Bucket": bucket.name, "ACL": bucket_acl},
        )
        bucket.set_acl(acl=bucket_acl)

        exo.boto_stub.add_response(
            "put_bucket_acl",
            {},
            {
                "Bucket": bucket.name,
                "AccessControlPolicy": {
                    "Grants": [
                        {
                            "Grantee": {
                                "DisplayName": bucket_acp.full_control,
                                "ID": bucket_acp.full_control,
                                "Type": "CanonicalUser",
                            },
                            "Permission": "FULL_CONTROL",
                        },
                        {
                            "Grantee": {
                                "DisplayName": bucket_acp.read,
                                "ID": bucket_acp.read,
                                "Type": "CanonicalUser",
                            },
                            "Permission": "READ",
                        },
                        {
                            "Grantee": {
                                "DisplayName": bucket_acp.write,
                                "ID": bucket_acp.write,
                                "Type": "CanonicalUser",
                            },
                            "Permission": "WRITE",
                        },
                        {
                            "Grantee": {
                                "DisplayName": bucket_acp.read_acp,
                                "ID": bucket_acp.read_acp,
                                "Type": "CanonicalUser",
                            },
                            "Permission": "READ_ACP",
                        },
                        {
                            "Grantee": {
                                "DisplayName": bucket_acp.write_acp,
                                "ID": bucket_acp.write_acp,
                                "Type": "CanonicalUser",
                            },
                            "Permission": "WRITE_ACP",
                        },
                    ],
                    "Owner": {
                        "DisplayName": bucket_acp.owner,
                        "ID": bucket_acp.owner,
                    },
                },
            },
        )

        bucket.set_acl(acp=bucket_acp)

    def test_set_cors(self, exo):
        bucket = Bucket(exo.storage, {}, _random_str())
        cors_rule_headers = ["*"]
        cors_rule_methods = ["GET"]
        cors_rule_origins = ["https://example.net/"]
        cors_rule_exposed_headers = ["X-Header1"]
        cors_rule_max_age_seconds = 3600

        exo.boto_stub.add_response(
            "put_bucket_cors",
            {},
            {
                "Bucket": bucket.name,
                "CORSConfiguration": {
                    "CORSRules": [
                        {
                            "AllowedHeaders": cors_rule_headers,
                            "AllowedMethods": cors_rule_methods,
                            "AllowedOrigins": cors_rule_origins,
                            "ExposeHeaders": cors_rule_exposed_headers,
                            "MaxAgeSeconds": cors_rule_max_age_seconds,
                        }
                    ]
                },
            },
        )

        bucket.set_cors(
            [
                CORSRule(
                    {},
                    allowed_headers=cors_rule_headers,
                    allowed_methods=cors_rule_methods,
                    allowed_origins=cors_rule_origins,
                    expose_headers=cors_rule_exposed_headers,
                    max_age_seconds=cors_rule_max_age_seconds,
                )
            ]
        )

    def test_delete(self, exo):
        bucket = Bucket(exo.storage, {}, _random_str())

        exo.boto_stub.add_response(
            "delete_bucket",
            {},
            {"Bucket": bucket.name},
        )

        bucket.delete()
        assert bucket.name is None

    def test_properties(self, exo):
        bucket_zone = "ch-gva-2"
        bucket = Bucket(exo.storage, {}, _random_str())

        exo.boto_stub.add_response(
            "get_bucket_location",
            {"LocationConstraint": bucket_zone},
            {"Bucket": bucket.name},
        )
        assert bucket.zone == bucket_zone

        exo.boto_stub.add_response(
            "get_bucket_location",
            {"LocationConstraint": bucket_zone},
            {"Bucket": bucket.name},
        )
        assert bucket.url == "https://sos-{}.exo.io/{}".format(
            bucket_zone, bucket.name
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
            "get_bucket_acl",
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
            {"Bucket": bucket.name},
        )
        actual_acp = bucket.acl
        assert actual_acp.full_control == expected_acp.full_control
        assert actual_acp.read == expected_acp.read
        assert actual_acp.write == expected_acp.write
        assert actual_acp.read_acp == expected_acp.read_acp
        assert actual_acp.write_acp == expected_acp.write_acp

        actual_cors_rule = CORSRule(
            {},
            allowed_headers=["*"],
            allowed_methods=["GET"],
            allowed_origins=["https://example.net/"],
            expose_headers=["X-Header1"],
            max_age_seconds=3600,
        )
        exo.boto_stub.add_response(
            "get_bucket_cors",
            {
                "CORSRules": [
                    {
                        "AllowedHeaders": actual_cors_rule.allowed_headers,
                        "AllowedMethods": actual_cors_rule.allowed_methods,
                        "AllowedOrigins": actual_cors_rule.allowed_origins,
                        "ExposeHeaders": actual_cors_rule.expose_headers,
                        "MaxAgeSeconds": actual_cors_rule.max_age_seconds,
                    }
                ]
            },
            {"Bucket": bucket.name},
        )
        expected_cors = list(bucket.cors)
        assert len(expected_cors) == 1
        assert (
            expected_cors[0].allowed_headers
            == actual_cors_rule.allowed_headers
        )
        assert (
            expected_cors[0].allowed_methods
            == actual_cors_rule.allowed_methods
        )
        assert (
            expected_cors[0].allowed_origins
            == actual_cors_rule.allowed_origins
        )
        assert (
            expected_cors[0].expose_headers == actual_cors_rule.expose_headers
        )
        assert (
            expected_cors[0].max_age_seconds
            == actual_cors_rule.max_age_seconds
        )
