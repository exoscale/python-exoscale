#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from exoscale.api.iam import APIKey
from urllib.parse import parse_qs, urlparse


class TestIAMAPIKey:
    def test_revoke(self, exo, apikey):
        api_key = APIKey._from_cs(exo.iam, apikey())

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["key"][0] == api_key.res["key"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {"revokeapikeyresponse": {"success": True}}

        exo.mock_get("?command=revokeApiKey", _assert_request)

        api_key.revoke()
        assert api_key.name is None
