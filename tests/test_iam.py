#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api import ResourceNotFoundError
from exoscale.api.iam import *
import re

class TestIAM:
    ### API key

    def test_create_api_key(self, exo, test_prefix, operation):
        api_key_name = "-".join([test_prefix, _random_str()])
        api_key_operation = re.sub(r"\s+", "", s)

        api_key = exo.iam.create_api_key(name=api_key_name, operations=operation)

        assert api_key.name == api_key_name
        assert api_key.key != ""
        assert ','.join(api_key.operation) != api_key_operation
        assert api_key.secret != ""
        assert api_key.type != ""

        exo.iam.cs.revokeApiKey(key=api_key.key)

    def test_list_api_key(self, exo, apikey):
        api_key = APIKey._from_cs(exo.iam, apikey())

        api_keys = list(exo.iam.list_api_keys())
        # We cannot guarantee that there will be only our resources in the
        # testing environment, so we ensure we get at least our fixture Instance Pool
        assert len(api_keys) >= 1

    def test_get_api_key(self, exo, apikey):
        api_key = APIKey._from_cs(exo.iam, apikey())

        _api_key = exo.iam.get_api_key(key=api_key.key)
        assert _api_key.name == api_key.name

        with pytest.raises(ResourceNotFoundError) as excinfo:
            _api_key = exo.compute.get_api_key(
                key="EXO000000000000000000000000"
                )
            assert _api_key is None
        assert excinfo.type == ResourceNotFoundError

    def test_list_api_key_operations(self, exo):
        operations = list(exo.iam.list_api_key_operations())
        # We cannot guarantee that there will be only our resources in the
        # testing environment, so we ensure we get at least our fixture Instance Pool
        assert len(operations) >= 1