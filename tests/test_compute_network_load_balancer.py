#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from .conftest import _random_str, _random_uuid
from exoscale.api.compute import InstancePool, NetworkLoadBalancer, Zone


class TestComputeNetworkLoadBalancer:
    def test_add_service(
        self,
        exo,
        zone,
        instance_type,
        instance_template,
        instance_pool,
        nlb,
        nlb_service,
    ):
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = Zone._from_cs(zone())
        instance_pool = InstancePool._from_api(
            exo.compute, instance_pool(), zone=zone
        )
        operation_id = _random_uuid()

        expected = nlb_service(
            **{
                "name": _random_str(),
                "description": _random_str(),
                "instance-pool": {"id": instance_pool.res["id"]},
                "port": 443,
                "target_port": 8443,
                "protocol": "tcp",
                "strategy": "source-hash",
                "healthcheck": {
                    "mode": "https",
                    "port": 8443,
                    "uri": "/health",
                    "interval": 10,
                    "timeout": 5,
                    "retries": 1,
                    "tls-sni": "example.net",
                },
            }
        )
        nlb = NetworkLoadBalancer._from_api(exo.compute, nlb(), zone=zone)

        def _assert_request(request, context):
            body = json.loads(request.body)
            assert body["name"] == expected["name"]
            assert body["description"] == expected["description"]
            assert body["instance-pool"]["id"] == instance_pool.res["id"]
            assert body["port"] == expected["port"]
            assert body["target-port"] == expected["target-port"]
            assert body["protocol"] == expected["protocol"]
            assert body["strategy"] == expected["strategy"]
            assert body["healthcheck"] == expected["healthcheck"]

            nlb.res["services"].append(expected)

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "id": operation_id,
                "state": "success",
                "reference": {"id": expected["id"]},
            }

        exo.mock_post(
            zone.res["name"],
            "load-balancer/{}/service".format(nlb.res["id"]),
            _assert_request,
        )
        exo.mock_get_operation(zone.res["name"], operation_id, nlb.res["id"])

        exo.mock_get_v2(
            zone.res["name"],
            "instance-pool/" + instance_pool.id,
            instance_pool.res,
        )
        exo.mock_get_v2(zone.res["name"], "load-balancer/" + nlb.id, nlb.res)

        actual = nlb.add_service(
            name=expected["name"],
            description=expected["description"],
            instance_pool=instance_pool,
            port=expected["port"],
            target_port=expected["target-port"],
            protocol=expected["protocol"],
            strategy=expected["strategy"],
            healthcheck_mode=expected["healthcheck"]["mode"],
            healthcheck_port=expected["healthcheck"]["port"],
            healthcheck_uri=expected["healthcheck"]["uri"],
            healthcheck_interval=expected["healthcheck"]["interval"],
            healthcheck_timeout=expected["healthcheck"]["timeout"],
            healthcheck_retries=expected["healthcheck"]["retries"],
            healthcheck_tls_sni=expected["healthcheck"]["tls-sni"],
        )
        assert actual.id == expected["id"]
        assert actual.name == expected["name"]
        assert actual.description == expected["description"]
        assert actual.instance_pool.id == instance_pool.res["id"]
        assert actual.port == expected["port"]
        assert actual.target_port == expected["target-port"]
        assert actual.protocol == expected["protocol"]
        assert actual.strategy == expected["strategy"]
        assert actual.healthcheck.mode == expected["healthcheck"]["mode"]
        assert actual.healthcheck.port == expected["healthcheck"]["port"]
        assert actual.healthcheck.uri == expected["healthcheck"]["uri"]
        assert (
            actual.healthcheck.interval == expected["healthcheck"]["interval"]
        )
        assert actual.healthcheck.timeout == expected["healthcheck"]["timeout"]
        assert actual.healthcheck.retries == expected["healthcheck"]["retries"]
        assert actual.healthcheck.tls_sni == expected["healthcheck"]["tls-sni"]

    def test_update(self, exo, zone, nlb):
        zone = Zone._from_cs(zone())
        nlb = NetworkLoadBalancer._from_api(exo.compute, nlb(), zone=zone)
        nlb_name = _random_str()
        nlb_description = _random_str()
        operation_id = _random_uuid()

        def _assert_request(request, context):
            body = json.loads(request.body)
            assert body["name"] == nlb_name
            assert body["description"] == nlb_description

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "id": operation_id,
                "state": "success",
                "reference": {"id": nlb.res["id"]},
            }

        exo.mock_put(
            zone.res["name"], "load-balancer/" + nlb.id, _assert_request
        )
        exo.mock_get_operation(zone.res["name"], operation_id, nlb.res["id"])

        nlb.update(name=nlb_name, description=nlb_description)
        assert nlb.name == nlb_name
        assert nlb.description == nlb_description

    def test_delete(self, exo, zone, nlb):
        zone = Zone._from_cs(zone())
        nlb = NetworkLoadBalancer._from_api(exo.compute, nlb(), zone=zone)
        operation_id = _random_uuid()

        def _assert_request(request, context):
            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "id": operation_id,
                "state": "success",
                "reference": {"id": nlb.res["id"]},
            }

        exo.mock_delete(
            zone.res["name"], "load-balancer/" + nlb.id, _assert_request
        )
        exo.mock_get_operation(zone.res["name"], operation_id, nlb.res["id"])

        nlb.delete()
        assert nlb.id is None

    def test_properties(
        self,
        exo,
        zone,
        instance_type,
        instance_template,
        instance_pool,
        nlb,
        nlb_service,
    ):
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = Zone._from_cs(zone())
        instance_pool = InstancePool._from_api(
            exo.compute, instance_pool(), zone=zone
        )
        nlb = NetworkLoadBalancer._from_api(
            exo.compute,
            nlb(
                services=[
                    nlb_service(
                        **{"instance-pool": {"id": instance_pool.res["id"]}}
                    )
                ]
            ),
            zone=zone,
        )

        exo.mock_get_v2(
            zone.res["name"],
            "instance-pool/" + instance_pool.id,
            instance_pool.res,
        )
        exo.mock_get_v2(zone.res["name"], "load-balancer/" + nlb.id, nlb.res)

        nlb_services = list(nlb.services)
        assert len(nlb_services) == 1
        assert nlb_services[0].id == nlb.res["services"][0]["id"]

        nlb_state = nlb.state
        assert nlb_state == "running"
