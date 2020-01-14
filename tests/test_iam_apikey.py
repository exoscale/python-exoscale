#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.iam import *
from .conftest import _random_str

class TestIAMAPIKey:
    def test_revoke(self, exo, apikey):
        api_key = APIKey._from_cs(exo.iam, apikey(teardown=False))
        api_key_key = api_key.key

        api_key.revoke()
        assert api_key.name is None

        res = exo.iam.cs.listApiKeys(key=api_key_key, fetch_list=True)
        assert len(res) == 0