#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.storage import *


class TestStorageBucket:
    def test_put_file(self, exo, bucket, tmp_path):
        bucket = Bucket(exo.storage, {}, bucket())

        f_a = tmp_path / "file_a"
        f_a.write_text("a")

        f = bucket.put_file(str(f_a), metadata={"k": "v"})
        assert f.path == "file_a"
        res = exo.storage.boto.get_object(Bucket=bucket.name, Key="file_a")
        assert res["Body"].read() == b"a"
        assert res["Metadata"] == {"k": "v"}

        f = bucket.put_file(str(f_a), "file_b")
        assert f.path == "file_b"
        res = exo.storage.boto.get_object(Bucket=bucket.name, Key="file_b")

        exo.storage.boto.delete_object(Bucket=bucket.name, Key="file_a")
        exo.storage.boto.delete_object(Bucket=bucket.name, Key="file_b")

    def test_list_files(self, exo, bucket, tmp_path):
        bucket = Bucket(exo.storage, {}, bucket())

        f_a = tmp_path / "file_a"
        f_a.write_text("a")
        f_b = tmp_path / "file_b"
        f_b.write_text("b")

        exo.storage.boto.upload_file(Bucket=bucket.name, Filename=str(f_a), Key="a/a")
        exo.storage.boto.upload_file(Bucket=bucket.name, Filename=str(f_b), Key="b")

        files = list(bucket.list_files())
        assert len(files) == 2
        assert files[0].path == "a/a"
        assert files[1].path == "b"

        files = list(bucket.list_files(prefix="a"))
        assert len(files) == 1
        assert files[0].path == "a/a"

        exo.storage.boto.delete_object(Bucket=bucket.name, Key="a/a")
        exo.storage.boto.delete_object(Bucket=bucket.name, Key="b")

    def test_get_file(self, exo, bucket, tmp_path):
        bucket = Bucket(exo.storage, {}, bucket())

        f_a = tmp_path / "file_a"
        f_a.write_text("a")

        exo.storage.boto.upload_file(Bucket=bucket.name, Filename=str(f_a), Key="a")

        file = bucket.get_file("a")
        assert file.path == "a"
        assert file.bucket.name == bucket.name

        exo.storage.boto.delete_object(Bucket=bucket.name, Key="a")

    def test_delete(self, exo, bucket):
        bucket = Bucket(exo.storage, {}, bucket(teardown=False))
        bucket_name = bucket.name

        bucket.delete()
        assert bucket.name == None

        res = exo.storage.boto.list_buckets()
        for i in res.get("Buckets", []):
            assert i["Name"] != bucket_name

    def test_set_acl(self, exo, bucket):
        bucket = Bucket(exo.storage, {}, bucket())

        bucket.set_acl(acl="public-read")
        res = exo.storage.boto.get_bucket_acl(Bucket=bucket.name)
        for i in res["Grants"]:
            if i["Permission"] == "READ":
                assert i["Grantee"]["Type"] == "Group"
                assert i["Grantee"]["URI"] == ACL_ALL_USERS

        bucket_acp = AccessControlPolicy.from_s3(res)
        bucket_acp.read = "ALL_USERS"
        bucket_acp.write = "AUTHENTICATED_USERS"
        bucket_acp.read_acp = "alice@example.net"
        bucket_acp.write_acp = "bob@example.net"
        bucket.set_acl(acp=bucket_acp)
        res = exo.storage.boto.get_bucket_acl(Bucket=bucket.name)
        for i in res["Grants"]:
            if i["Permission"] == "READ":
                assert i["Grantee"]["Type"] == "Group"
                assert i["Grantee"]["URI"] == ACL_ALL_USERS
            if i["Permission"] == "WRITE":
                assert i["Grantee"]["Type"] == "Group"
                assert i["Grantee"]["URI"] == ACL_AUTHENTICATED_USERS
            if i["Permission"] == "READ_ACP":
                assert i["Grantee"]["Type"] == "CanonicalUser"
                assert i["Grantee"]["ID"] == "alice@example.net"
                assert i["Grantee"]["DisplayName"] == "alice@example.net"
            if i["Permission"] == "WRITE_ACP":
                assert i["Grantee"]["Type"] == "CanonicalUser"
                assert i["Grantee"]["ID"] == "bob@example.net"
                assert i["Grantee"]["DisplayName"] == "bob@example.net"

    def test_set_cors(self, exo, bucket):
        bucket = Bucket(exo.storage, {}, bucket())

        bucket.set_cors(
            [
                CORSRule(
                    {},
                    allowed_headers=["*"],
                    allowed_methods=["GET"],
                    allowed_origins=["https://example.net/"],
                    expose_headers=["X-Header1"],
                    max_age_seconds=3600,
                )
            ]
        )
        res = exo.storage.boto.get_bucket_cors(Bucket=bucket.name)
        assert len(res["CORSRules"]) == 1
        assert res["CORSRules"][0]["AllowedHeaders"] == ["*"]
        assert res["CORSRules"][0]["AllowedMethods"] == ["GET"]
        assert res["CORSRules"][0]["AllowedOrigins"] == ["https://example.net/"]
        assert res["CORSRules"][0]["ExposeHeaders"] == ["X-Header1"]
        assert res["CORSRules"][0]["MaxAgeSeconds"] == 3600

    def test_properties(self, exo, bucket):
        bucket = Bucket(exo.storage, {}, bucket(zone="ch-gva-2"))
        assert bucket.zone == "ch-gva-2"

        exo.storage.boto.put_bucket_acl(
            Bucket=bucket.name,
            AccessControlPolicy={
                "Grants": [
                    {
                        "Grantee": {
                            "DisplayName": "alice@example.net",
                            "ID": "alice@example.net",
                            "Type": "CanonicalUser",
                        },
                        "Permission": "FULL_CONTROL",
                    },
                    {
                        "Grantee": {"Type": "Group", "URI": ACL_ALL_USERS},
                        "Permission": "READ",
                    },
                    {
                        "Grantee": {"Type": "Group", "URI": ACL_AUTHENTICATED_USERS},
                        "Permission": "WRITE",
                    },
                    {
                        "Grantee": {
                            "DisplayName": "bob@example.net",
                            "ID": "bob@example.net",
                            "Type": "CanonicalUser",
                        },
                        "Permission": "READ_ACP",
                    },
                    {
                        "Grantee": {
                            "DisplayName": "carl@example.net",
                            "ID": "carl@example.net",
                            "Type": "CanonicalUser",
                        },
                        "Permission": "WRITE_ACP",
                    },
                ]
            },
        )
        acp = bucket.acl
        assert acp.full_control == "alice@example.net"
        assert acp.read == "ALL_USERS"
        assert acp.write == "AUTHENTICATED_USERS"
        assert acp.read_acp == "bob@example.net"
        assert acp.write_acp == "carl@example.net"

        exo.storage.boto.put_bucket_cors(
            Bucket=bucket.name,
            CORSConfiguration={
                "CORSRules": [
                    {
                        "AllowedHeaders": ["*"],
                        "AllowedMethods": ["GET"],
                        "AllowedOrigins": ["https://example.net/"],
                        "ExposeHeaders": ["X-Header1"],
                        "MaxAgeSeconds": 3600,
                    }
                ]
            },
        )
        cors = list(bucket.cors)
        assert len(cors) == 1
        assert cors[0].allowed_headers == ["*"]
        assert cors[0].allowed_methods == ["GET"]
        assert cors[0].allowed_origins == ["https://example.net/"]
        assert cors[0].expose_headers == ["X-Header1"]
        assert cors[0].max_age_seconds == 3600
