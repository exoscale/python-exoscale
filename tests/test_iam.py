#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api import ResourceNotFoundError
from exoscale.api.iam import *
from .conftest import _random_str
from urllib.parse import parse_qs, urljoin, urlparse


class TestIAM:
    ### API key

    def test_create_api_key(self, exo, apikey):
        api_key_name = _random_str()
        api_key_operations = ["compute/listZones"]
        expected = apikey(
            name=api_key_name, secret=_random_str(), operations=api_key_operations
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["name"][0] == api_key_name
            assert params["operations"] == api_key_operations

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {"createapikeyresponse": {"apikey": expected}}

        exo.mock_get("?command=createApiKey", _assert_request)

        actual = exo.iam.create_api_key(
            name=api_key_name, operations=api_key_operations
        )

        assert actual.name == expected["name"]
        assert actual.key == expected["key"]
        assert actual.secret == expected["secret"]
        assert actual.type == expected["type"]
        assert actual.operations == expected["operations"]

    def test_list_api_keys(self, exo, apikey):
        expected = apikey()

        exo.mock_list("listApiKeys", [expected])
        actual = list(exo.iam.list_api_keys())
        assert len(actual) == 1
        assert actual[0].key == expected["key"]

    def test_get_api_key(self, exo, apikey):
        expected = apikey()

        exo.mock_get(
            "?command=getApiKey&key={}".format(expected["key"]),
            {"getapikeyreponse": expected},
        )
        actual = exo.iam.get_api_key(key=expected["key"])
        assert actual.key == expected["key"]

        with pytest.raises(ResourceNotFoundError) as excinfo:
            exo.mocker.get(
                urljoin(exo.iam.endpoint, "?command=getApiKey&key=lolnope"),
                status_code=404,
                json={"errorresponse": {"errortext": "The key is not found."}},
                headers={"Content-Type": "application/json"},
            )
            actual = exo.iam.get_api_key(key="lolnope")
            assert actual is None
        assert excinfo.type == ResourceNotFoundError

    def test_list_api_key_operations(self, exo):
        expected = ["compute/listZones"]

        exo.mock_get(
            "?command=listApiKeyOperations",
            {"listapikeyoperationsresponse": {"operations": expected}},
        )

        assert list(exo.iam.list_api_key_operations()) == expected
