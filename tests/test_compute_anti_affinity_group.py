#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.compute import *
from urllib.parse import parse_qs, urljoin, urlparse
from .conftest import _random_uuid


class TestComputeAntiAffinityGroup:
    def test_delete(self, exo, aag):
        anti_affinity_group = AntiAffinityGroup._from_cs(exo.compute, aag())

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == anti_affinity_group.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "deleteffinitygroupresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=deleteAffinityGroup", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        anti_affinity_group.delete()
        assert anti_affinity_group.id is None
