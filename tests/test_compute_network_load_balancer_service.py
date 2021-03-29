#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from .conftest import _random_str, _random_uuid
from exoscale.api.compute import *
from urllib.parse import parse_qs, urlparse


class TestComputeNetworkLoadBalancerService:
    def test_update(
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
        instance_pool = InstancePool._from_cs(
            exo.compute, instance_pool(zone_id=zone.id), zone=zone
        )
        nlb_service = nlb_service()
        nlb_service_name = _random_str()
        nlb_service_description = _random_str()
        nlb_service_instance_pool = instance_pool.res["id"]
        nlb_service_port = 443
        nlb_service_target_port = 8443
        nlb_service_protocol = "tcp"
        nlb_service_strategy = "source-hash"
        nlb_service_healthcheck_mode = "https"
        nlb_service_healthcheck_port = 8443
        nlb_service_healthcheck_uri = "/health"
        nlb_service_healthcheck_interval = 10
        nlb_service_healthcheck_timeout = 5
        nlb_service_healthcheck_retries = 1
        nlb_service_healthcheck_tls_sni = "example.net"
        nlb = NetworkLoadBalancer._from_api(
            exo.compute, nlb(services=[nlb_service]), zone=zone
        )
        operation_id = _random_uuid()

        exo.mock_get(
            "?command=getInstancePool",
            {
                "getinstancepoolresponse": {
                    "count": 1,
                    "instancepool": [instance_pool.res],
                }
            },
        )

        def _assert_request(request, context):
            body = json.loads(request.body)
            assert body["name"] == nlb_service_name
            assert body["description"] == nlb_service_description
            assert body["port"] == nlb_service_port
            assert body["target-port"] == nlb_service_target_port
            assert body["protocol"] == nlb_service_protocol
            assert body["strategy"] == nlb_service_strategy
            assert body["healthcheck"]["mode"] == nlb_service_healthcheck_mode
            assert body["healthcheck"]["port"] == nlb_service_healthcheck_port
            assert body["healthcheck"]["uri"] == nlb_service_healthcheck_uri
            assert body["healthcheck"]["interval"] == nlb_service_healthcheck_interval
            assert body["healthcheck"]["timeout"] == nlb_service_healthcheck_timeout
            assert body["healthcheck"]["retries"] == nlb_service_healthcheck_retries
            assert body["healthcheck"]["tls-sni"] == nlb_service_healthcheck_tls_sni

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "id": operation_id,
                "state": "success",
                "reference": {"id": nlb.res["id"]},
            }

        exo.mock_put(
            zone.res["name"],
            "load-balancer/{}/service/{}".format(nlb.res["id"], nlb_service["id"]),
            _assert_request,
        )
        exo.mock_get_operation(zone.res["name"], operation_id, nlb.res["id"])

        exo.mock_get_v2(
            zone.res["name"], "load-balancer/{}".format(nlb.res["id"]), nlb.res
        )

        actual = list(nlb.services)[0]
        actual.update(
            name=nlb_service_name,
            description=nlb_service_description,
            port=nlb_service_port,
            target_port=nlb_service_target_port,
            protocol=nlb_service_protocol,
            strategy=nlb_service_strategy,
            healthcheck_mode=nlb_service_healthcheck_mode,
            healthcheck_port=nlb_service_healthcheck_port,
            healthcheck_uri=nlb_service_healthcheck_uri,
            healthcheck_interval=nlb_service_healthcheck_interval,
            healthcheck_timeout=nlb_service_healthcheck_timeout,
            healthcheck_retries=nlb_service_healthcheck_retries,
            healthcheck_tls_sni=nlb_service_healthcheck_tls_sni,
        )
        assert actual.name == nlb_service_name
        assert actual.description == nlb_service_description
        assert actual.instance_pool.id == instance_pool.res["id"]
        assert actual.port == nlb_service_port
        assert actual.target_port == nlb_service_target_port
        assert actual.protocol == nlb_service_protocol
        assert actual.strategy == nlb_service_strategy
        assert actual.healthcheck.mode == nlb_service_healthcheck_mode
        assert actual.healthcheck.port == nlb_service_healthcheck_port
        assert actual.healthcheck.uri == nlb_service_healthcheck_uri
        assert actual.healthcheck.interval == nlb_service_healthcheck_interval
        assert actual.healthcheck.timeout == nlb_service_healthcheck_timeout
        assert actual.healthcheck.retries == nlb_service_healthcheck_retries
        assert actual.healthcheck.tls_sni == nlb_service_healthcheck_tls_sni

    def test_delete(
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
        instance_pool = InstancePool._from_cs(
            exo.compute, instance_pool(zone_id=zone.id), zone=zone
        )
        nlb_service = nlb_service()
        nlb = NetworkLoadBalancer._from_api(
            exo.compute, nlb(services=[nlb_service]), zone=zone
        )
        operation_id = _random_uuid()

        exo.mock_get(
            "?command=getInstancePool",
            {
                "getinstancepoolresponse": {
                    "count": 1,
                    "instancepool": [instance_pool.res],
                }
            },
        )

        def _assert_request(request, context):
            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "id": operation_id,
                "state": "success",
                "reference": {"id": nlb.res["id"]},
            }

        exo.mock_delete(
            zone.res["name"],
            "load-balancer/{}/service/{}".format(nlb.res["id"], nlb_service["id"]),
            _assert_request,
        )
        exo.mock_get_operation(zone.res["name"], operation_id, nlb.res["id"])

        exo.mock_get_v2(
            zone.res["name"], "load-balancer/{}".format(nlb.res["id"]), nlb.res
        )

        actual = list(nlb.services)[0]
        actual.delete()
        assert actual.id is None

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
        instance_pool = InstancePool._from_cs(
            exo.compute, instance_pool(zone_id=zone.id), zone=zone
        )
        nlb_service = nlb_service()
        nlb = NetworkLoadBalancer._from_api(
            exo.compute, nlb(services=[nlb_service]), zone=zone
        )

        exo.mock_get(
            "?command=getInstancePool",
            {
                "getinstancepoolresponse": {
                    "count": 1,
                    "instancepool": [instance_pool.res],
                }
            },
        )

        exo.mock_get_v2(
            zone.res["name"], "load-balancer/{}".format(nlb.res["id"]), nlb.res
        )
        exo.mock_get_v2(
            zone.res["name"],
            "load-balancer/{}/service/{}".format(nlb.res["id"], nlb_service["id"]),
            nlb_service,
        )

        actual = list(nlb.services)[0]
        assert actual.state == "running"
        assert len(actual.healthcheck_status) > 0
