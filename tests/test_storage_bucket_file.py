#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from datetime import datetime
from exoscale.api.storage import *


class TestStorageBucketFile:
    def test_delete(self, exo, bucket, tmp_path):
        bucket = Bucket(exo.storage, {}, bucket())

        f_a = tmp_path / "file_a"
        f_a.write_text("a")
        exo.storage.boto.upload_file(Bucket=bucket.name, Filename=str(f_a), Key="a")

        f = BucketFile(exo.storage, {}, path="a", bucket=bucket)
        f.delete()

        res = exo.storage.boto.list_objects(Bucket=bucket.name)
        assert "Contents" not in res

    def test_set_acl(self, exo, bucket, tmp_path):
        bucket = Bucket(exo.storage, {}, bucket())

        f_a = tmp_path / "file_a"
        f_a.write_text("a")
        exo.storage.boto.upload_file(Bucket=bucket.name, Filename=str(f_a), Key="a")

        f = BucketFile(exo.storage, {}, path="a", bucket=bucket)
        f.set_acl(acl="public-read")
        res = exo.storage.boto.get_object_acl(Bucket=bucket.name, Key="a")
        for i in res["Grants"]:
            if i["Permission"] == "READ":
                assert i["Grantee"]["Type"] == "Group"
                assert i["Grantee"]["URI"] == ACL_ALL_USERS

        f_acp = AccessControlPolicy.from_s3(res)
        f_acp.read = "ALL_USERS"
        f_acp.write = "AUTHENTICATED_USERS"
        f_acp.read_acp = "alice@example.net"
        f_acp.write_acp = "bob@example.net"
        f.set_acl(acp=f_acp)
        res = exo.storage.boto.get_object_acl(Bucket=bucket.name, Key="a")
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

        exo.storage.boto.delete_object(Bucket=bucket.name, Key="a")

    def test_properties(self, exo, bucket, tmp_path):
        bucket = Bucket(exo.storage, {}, bucket())

        f_a = tmp_path / "file_a"
        f_a.write_text("a")
        exo.storage.boto.upload_file(
            Bucket=bucket.name,
            Filename=str(f_a),
            Key="a",
            ExtraArgs={"Metadata": {"k": "v"}},
        )

        f = BucketFile(exo.storage, {}, path="a", bucket=bucket)
        assert f.size == len(f_a.read_text())
        assert type(f.last_modification_date) == datetime
        assert f.metadata == {"k": "v"}
        assert f.content.read() == b"a"
        file_url = f.url
        assert file_url.startswith("https://sos-") and file_url.endswith("/a")

        # We retrieve the current owner of the file to maintain it in the updated ACP,
        # otherwise we'll lock ourselves out and we won't be able to delete the file
        # afterwards
        owner_id = exo.storage.boto.get_object_acl(Bucket=bucket.name, Key="a")[
            "Owner"
        ]["ID"]

        exo.storage.boto.put_object_acl(
            Bucket=bucket.name,
            Key="a",
            AccessControlPolicy={
                "Grants": [
                    {
                        "Grantee": {
                            "DisplayName": owner_id,
                            "ID": owner_id,
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
        acp = f.acl
        assert acp.full_control == owner_id
        assert acp.read == "ALL_USERS"
        assert acp.write == "AUTHENTICATED_USERS"
        assert acp.read_acp == "bob@example.net"
        assert acp.write_acp == "carl@example.net"

        exo.storage.boto.delete_object(Bucket=bucket.name, Key="a")
