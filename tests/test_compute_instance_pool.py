#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from .conftest import _random_str, _random_uuid
from base64 import b64decode
from exoscale.api.compute import *
from urllib.parse import parse_qs, urlparse


class TestComputeInstancePool:
    def test_update(self, exo, zone, instance_type, instance_template, instance_pool):
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        instance_pool = InstancePool._from_cs(
            exo.compute, instance_pool(zone_id=zone["id"]), zone=Zone._from_cs(zone)
        )
        instance_pool_name = _random_str()
        instance_pool_description = _random_str()
        instance_pool_type = InstanceType._from_cs(instance_type())
        instance_pool_template = InstanceTemplate._from_cs(
            exo.compute, instance_template(), Zone._from_cs(zone)
        )
        instance_pool_volume_size = instance_pool.instance_volume_size * 2
        instance_pool_user_data = _random_str()

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["zoneid"][0] == zone["id"]
            assert params["id"][0] == instance_pool.res["id"]
            assert params["name"][0] == instance_pool_name
            assert params["description"][0] == instance_pool_description
            assert params["templateid"][0] == instance_pool_template.res["id"]
            assert params["serviceofferingid"][0] == instance_pool_type.res["id"]
            assert params["rootdisksize"][0] == str(instance_pool_volume_size)
            assert (
                b64decode(params["userdata"][0]).decode("utf-8")
                == instance_pool_user_data
            )

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "createinstancepoolresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=updateInstancePool", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        instance_pool.update(
            name=instance_pool_name,
            description=instance_pool_description,
            instance_type=instance_pool_type,
            instance_template=instance_pool_template,
            instance_volume_size=instance_pool_volume_size,
            instance_user_data=instance_pool_user_data,
        )
        assert instance_pool.name == instance_pool_name
        assert instance_pool.description == instance_pool_description
        assert instance_pool.instance_type.id == instance_pool_type.res["id"]
        assert instance_pool.instance_template.id == instance_pool_template.res["id"]
        assert instance_pool.instance_volume_size == instance_pool_volume_size
        assert (
            b64decode(instance_pool.instance_user_data).decode("utf-8")
            == instance_pool_user_data
        )

    def test_scale(self, exo, zone, instance_type, instance_template, instance_pool):
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        instance_pool = InstancePool._from_cs(
            exo.compute, instance_pool(zone_id=zone["id"]), zone=Zone._from_cs(zone)
        )
        instance_pool_size = 3

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["zoneid"][0] == zone["id"]
            assert params["id"][0] == instance_pool.res["id"]
            assert params["size"][0] == str(instance_pool_size)

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "createinstancepoolresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=scaleInstancePool", _assert_request)
        exo.mock_query_async_job_result(instance_pool.res)

        instance_pool.scale(instance_pool_size)
        assert instance_pool.size == instance_pool_size

    def test_delete(self, exo, zone, instance_type, instance_template, instance_pool):
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        instance_pool = InstancePool._from_cs(
            exo.compute, instance_pool(zone_id=zone["id"]), Zone._from_cs(zone)
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["zoneid"][0] == zone["id"]
            assert params["id"][0] == instance_pool.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "removeipfromnicresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=destroyInstancePool", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        instance_pool.delete(wait=False)
        assert instance_pool.id is None

    def test_properties(
        self,
        exo,
        zone,
        aag,
        sg,
        privnet,
        instance_type,
        instance_template,
        instance_pool,
    ):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        anti_affinity_group = AntiAffinityGroup._from_cs(exo.compute, aag())
        security_group = SecurityGroup._from_cs(exo.compute, sg())
        private_network = PrivateNetwork._from_cs(
            exo.compute, privnet(), zone=Zone._from_cs(zone)
        )
        instance_pool = InstancePool._from_cs(
            exo.compute,
            instance_pool(
                zone_id=zone["id"],
                size=1,
                anti_affinity_group_ids=[anti_affinity_group.id],
                security_group_ids=[security_group.id],
                private_network_ids=[private_network.id],
            ),
            zone=Zone._from_cs(zone),
        )

        exo.mock_list("listAffinityGroups", [anti_affinity_group.res])
        exo.mock_list("listSecurityGroups", [security_group.res])
        exo.mock_list("listNetworks", [private_network.res])
        exo.mock_get(
            "?command=getInstancePool",
            {
                "getinstancepoolresponse": {
                    "count": 1,
                    "instancepool": [instance_pool.res],
                }
            },
        )

        instance_pool_instances = list(instance_pool.instances)
        assert len(instance_pool_instances) == 1
        assert instance_pool_instances[0].instance_pool.id == instance_pool.id

        instance_pool_anti_affinity_groups = list(instance_pool.anti_affinity_groups)
        assert len(instance_pool_anti_affinity_groups) == 1
        assert instance_pool_anti_affinity_groups[0].id == anti_affinity_group.id

        instance_pool_security_groups = list(instance_pool.security_groups)
        assert len(instance_pool_security_groups) == 1
        assert instance_pool_security_groups[0].id == security_group.id

        instance_pool_private_networks = list(instance_pool.private_networks)
        assert len(instance_pool_private_networks) == 1
        assert instance_pool_private_networks[0].id == private_network.id
