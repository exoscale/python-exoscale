#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from .conftest import _random_str, _random_uuid
from exoscale.api.compute import *
from urllib.parse import parse_qs, urlparse


class TestComputeInstanceVolumeSnapshot:
    def test_export(self, exo, zone, volume_snapshot):
        snapshot = InstanceVolumeSnapshot._from_cs(exo.compute, volume_snapshot())

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == snapshot.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "exportsnapshotresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=exportSnapshot", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        snapshot.export()

    def test_revert(
        self, exo, zone, volume_snapshot, instance_type, instance_template, instance
    ):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        instance = Instance._from_cs(
            exo.compute, instance(), zone=Zone._from_cs(zone())
        )
        snapshot = InstanceVolumeSnapshot._from_cs(exo.compute, volume_snapshot())

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == snapshot.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "exportsnapshotresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=revertSnapshot", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        snapshot.revert()

    def test_delete(self, exo, volume_snapshot):
        snapshot = InstanceVolumeSnapshot._from_cs(exo.compute, volume_snapshot())

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == snapshot.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "deletesnapshotresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=deleteSnapshot", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        snapshot.delete()
        assert snapshot.id is None

    def test_properties(self, exo, volume_snapshot):
        snapshot = InstanceVolumeSnapshot._from_cs(exo.compute, volume_snapshot())

        exo.mock_list("listSnapshots", [snapshot.res])

        assert snapshot.state == "exported"
