#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.compute import *

class TestIAMAPIKey:
    def test_revoke(self, exo, apikey):
        api_key = APIKey._from_cs(exo.compute, apikey(teardown=False))
        api_key_key = api_key.key

        api_key.delete()
        assert api_key.name is None

        res = exo.compute.cs.listApiKeys(key=api_key_key, fetch_list=True)
        assert len(res) == 0