#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .conftest import _random_uuid
from exoscale.api.compute import SSHKey
from urllib.parse import parse_qs, urlparse


class TestComputeSSHKey:
    def test_delete(self, exo, sshkey):
        ssh_key = SSHKey._from_cs(exo.compute, sshkey())

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["name"][0] == ssh_key.res["name"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "deletesshkeypairresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=deleteSSHKeyPair", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        ssh_key.delete()
        assert ssh_key.name is None
