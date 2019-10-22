#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api import ResourceNotFoundError
from exoscale.api.iam import *
from .conftest import _random_str


class TestIAM:
    ### API key

    def test_create_api_key(self, exo, test_prefix):
        api_key_name = "-".join([test_prefix, _random_str()])

        api_key = exo.iam.create_api_key(name=api_key_name)

        assert api_key.name == api_key_name
        assert api_key.key != ""
        assert api_key.operations != ""
        assert api_key.secret != ""
        assert api_key.type != ""

        exo.iam.cs.revokeApiKey(key=api_key.key)

    def test_list_api_key(self, exo, apikey):
        api_key = APIKey._from_cs(exo.iam, apikey())

        api_keys = list(exo.iam.list_api_keys())

        assert len(api_keys) >= 1

    def test_get_api_key(self, exo, apikey):
        api_key = APIKey._from_cs(exo.iam, apikey())

        _api_key = exo.iam.get_api_key(key=api_key.key)
        assert _api_key.name == api_key.name

        with pytest.raises(ResourceNotFoundError) as excinfo:
            _api_key = exo.iam.get_api_key(key="EXO000000000000000000000000")
            assert _api_key is None
        assert excinfo.type == ResourceNotFoundError

    def test_list_api_key_operations(self, exo):
        operations = list(exo.iam.list_api_key_operations())

        assert len(operations) >= 1
