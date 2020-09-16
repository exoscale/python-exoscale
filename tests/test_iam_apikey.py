#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.iam import *


class TestIAMAPIKey:
    def test_revoke(self, exo, apikey):
        api_key = APIKey._from_cs(exo.iam, apikey(teardown=False))
        api_key_id = api_key.key

        api_key.revoke()
        assert api_key.name is None

        with pytest.raises(CloudStackApiException) as excinfo:
            _api_key = exo.iam.cs.getApiKey(key=api_key_id)
            assert _api_key is None
        assert excinfo.type == CloudStackApiException
