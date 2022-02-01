#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from .conftest import _random_str
from exoscale.api import ResourceNotFoundError
from exoscale.api.storage import (
    ACL_ALL_USERS,
    ACL_AUTHENTICATED_USERS,
    AccessControlPolicy,
    CORSRule,
)


class TestStorage:
    # Bucket

    def test_create_bucket(self, exo, zone):
        zone = zone()
        bucket_name = _random_str()
        bucket_acl = "public-read"

        exo.boto_stub.add_response(
            "create_bucket",
            {},
            {
                "Bucket": bucket_name,
                "ACL": bucket_acl,
                "CreateBucketConfiguration": {
                    "LocationConstraint": zone["name"]
                },
            },
        )

        actual = exo.storage.create_bucket(
            zone=zone["name"], name=bucket_name, acl=bucket_acl
        )
        assert actual.name == bucket_name

    def test_list_buckets(self, exo):
        exo.boto_stub.add_response(
            "list_buckets",
            {"Buckets": [{"Name": _random_str()} for i in range(3)]},
        )

        actual = list(exo.storage.list_buckets())
        assert len(actual) == 3

    def test_get_bucket(self, exo):
        bucket_name = _random_str()

        exo.boto_stub.add_response(
            "list_buckets",
            {"Buckets": [{"Name": bucket_name}]},
        )

        actual = exo.storage.get_bucket(name=bucket_name)
        assert actual.name == bucket_name

        with pytest.raises(ResourceNotFoundError) as excinfo:
            exo.boto_stub.add_response("list_buckets", {"Buckets": []})
            actual = exo.storage.get_bucket(name="lolnope")
            assert actual is None
        assert excinfo.type == ResourceNotFoundError

    # CORSRule

    def test_cors_rule_from_s3(self):
        cors_rule_allowed_headers = ["*"]
        cors_rule_allowed_methods = ["GET"]
        cors_rule_allowed_origins = ["https://example.net/"]
        cors_rule_exposed_headers = ["X-Header1"]
        cors_rule_max_age_seconds = 3600
        cors_rule = {
            "AllowedHeaders": cors_rule_allowed_headers,
            "AllowedMethods": cors_rule_allowed_methods,
            "AllowedOrigins": cors_rule_allowed_origins,
            "ExposeHeaders": cors_rule_exposed_headers,
            "MaxAgeSeconds": cors_rule_max_age_seconds,
        }

        expected = CORSRule(
            cors_rule,
            allowed_headers=cors_rule_allowed_headers,
            allowed_methods=cors_rule_allowed_methods,
            allowed_origins=cors_rule_allowed_origins,
            expose_headers=cors_rule_exposed_headers,
            max_age_seconds=cors_rule_max_age_seconds,
        )

        actual = CORSRule._from_s3(cors_rule)
        assert actual == expected

    def test_cors_rule_to_s3(self):
        cors_rule_allowed_headers = ["*"]
        cors_rule_allowed_methods = ["GET"]
        cors_rule_allowed_origins = ["https://example.net/"]
        cors_rule_exposed_headers = ["X-Header1"]
        cors_rule_max_age_seconds = 3600

        cors_rule = CORSRule(
            {},
            allowed_headers=cors_rule_allowed_headers,
            allowed_methods=cors_rule_allowed_methods,
            allowed_origins=cors_rule_allowed_origins,
            expose_headers=cors_rule_exposed_headers,
            max_age_seconds=cors_rule_max_age_seconds,
        )

        assert cors_rule._to_s3() == {
            "AllowedHeaders": cors_rule_allowed_headers,
            "AllowedMethods": cors_rule_allowed_methods,
            "AllowedOrigins": cors_rule_allowed_origins,
            "ExposeHeaders": cors_rule_exposed_headers,
            "MaxAgeSeconds": cors_rule_max_age_seconds,
        }

    # AccessControlPolicy

    def test_access_control_policy_grantee_from_s3(self):
        grantee_id = _random_str()
        grantee_name = _random_str()

        with pytest.raises(ValueError) as excinfo:
            AccessControlPolicy._grantee_from_s3(
                None,
                {"URI": "lolnope", "Type": "Group"},
            )
        assert excinfo.type == ValueError

        actual = AccessControlPolicy._grantee_from_s3(
            None,
            {
                "DisplayName": grantee_name,
                "ID": grantee_id,
                "Type": "CanonicalUser",
            },
        )
        assert actual == grantee_name

        actual = AccessControlPolicy._grantee_from_s3(
            None,
            {"Type": "Group", "URI": ACL_ALL_USERS},
        )
        assert actual == "ALL_USERS"

        actual = AccessControlPolicy._grantee_from_s3(
            None,
            {"Type": "Group", "URI": ACL_AUTHENTICATED_USERS},
        )
        assert actual == "AUTHENTICATED_USERS"

    def test_access_control_policy_grantee_to_s3(self):
        grantee_id = _random_str()

        actual = AccessControlPolicy._grantee_to_s3(None, grantee_id)
        assert actual == {
            "Type": "CanonicalUser",
            "ID": grantee_id,
            "DisplayName": grantee_id,
        }

        actual = AccessControlPolicy._grantee_to_s3(None, "ALL_USERS")
        assert actual == {"Type": "Group", "URI": ACL_ALL_USERS}

        actual = AccessControlPolicy._grantee_to_s3(
            None, "AUTHENTICATED_USERS"
        )
        assert actual == {"Type": "Group", "URI": ACL_AUTHENTICATED_USERS}

    def test_access_control_policy_from_s3(self):
        acp_read = _random_str()
        acp_write = _random_str()
        acp_read_acp = _random_str()
        acp_write_acp = _random_str()
        acp_full_control = _random_str()
        acp_owner = _random_str()
        acp = {
            "Grants": [
                {
                    "Grantee": {
                        "DisplayName": acp_full_control,
                        "ID": acp_full_control,
                        "Type": "CanonicalUser",
                    },
                    "Permission": "FULL_CONTROL",
                },
                {
                    "Grantee": {
                        "DisplayName": acp_read,
                        "ID": acp_read,
                        "Type": "CanonicalUser",
                    },
                    "Permission": "READ",
                },
                {
                    "Grantee": {
                        "DisplayName": acp_write,
                        "ID": acp_write,
                        "Type": "CanonicalUser",
                    },
                    "Permission": "WRITE",
                },
                {
                    "Grantee": {
                        "DisplayName": acp_read_acp,
                        "ID": acp_read_acp,
                        "Type": "CanonicalUser",
                    },
                    "Permission": "READ_ACP",
                },
                {
                    "Grantee": {
                        "DisplayName": acp_write_acp,
                        "ID": acp_write_acp,
                        "Type": "CanonicalUser",
                    },
                    "Permission": "WRITE_ACP",
                },
            ],
            "Owner": {"DisplayName": acp_owner, "ID": acp_owner},
        }

        actual = AccessControlPolicy._from_s3(acp)
        assert actual.read == acp_read
        assert actual.write == acp_write
        assert actual.read_acp == acp_read_acp
        assert actual.write_acp == acp_write_acp
        assert actual.full_control == acp_full_control
        assert actual.owner == acp_owner

    def test_access_control_policy_to_s3(self):
        acp_read = _random_str()
        acp_write = _random_str()
        acp_read_acp = _random_str()
        acp_write_acp = _random_str()
        acp_full_control = _random_str()
        acp_owner = _random_str()

        acl = AccessControlPolicy(
            {},
            owner=acp_owner,
            read=acp_read,
            write=acp_write,
            read_acp=acp_read_acp,
            write_acp=acp_write_acp,
            full_control=acp_full_control,
        )

        assert acl._to_s3() == {
            "Grants": [
                {
                    "Grantee": {
                        "DisplayName": acp_full_control,
                        "ID": acp_full_control,
                        "Type": "CanonicalUser",
                    },
                    "Permission": "FULL_CONTROL",
                },
                {
                    "Grantee": {
                        "DisplayName": acp_read,
                        "ID": acp_read,
                        "Type": "CanonicalUser",
                    },
                    "Permission": "READ",
                },
                {
                    "Grantee": {
                        "DisplayName": acp_write,
                        "ID": acp_write,
                        "Type": "CanonicalUser",
                    },
                    "Permission": "WRITE",
                },
                {
                    "Grantee": {
                        "DisplayName": acp_read_acp,
                        "ID": acp_read_acp,
                        "Type": "CanonicalUser",
                    },
                    "Permission": "READ_ACP",
                },
                {
                    "Grantee": {
                        "DisplayName": acp_write_acp,
                        "ID": acp_write_acp,
                        "Type": "CanonicalUser",
                    },
                    "Permission": "WRITE_ACP",
                },
            ],
            "Owner": {"DisplayName": acp_owner, "ID": acp_owner},
        }
