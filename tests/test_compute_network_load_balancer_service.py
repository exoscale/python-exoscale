#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from .conftest import _random_str, _random_uuid
from exoscale.api.compute import InstancePool, NetworkLoadBalancer, Zone


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
        instance_pool = InstancePool._from_api(
            exo.compute, instance_pool(), zone=zone
        )
        nlb_service = nlb_service(
            **{"instance-pool": {"id": instance_pool.id}}
        )
        nlb_service_name = _random_str()
        nlb_service_description = _random_str()
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
            assert (
                body["healthcheck"]["interval"]
                == nlb_service_healthcheck_interval
            )
            assert (
                body["healthcheck"]["timeout"]
                == nlb_service_healthcheck_timeout
            )
            assert (
                body["healthcheck"]["retries"]
                == nlb_service_healthcheck_retries
            )
            assert (
                body["healthcheck"]["tls-sni"]
                == nlb_service_healthcheck_tls_sni
            )

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "id": operation_id,
                "state": "success",
                "reference": {"id": nlb.res["id"]},
            }

        exo.mock_put(
            zone.res["name"],
            "load-balancer/{}/service/{}".format(
                nlb.res["id"], nlb_service["id"]
            ),
            _assert_request,
        )
        exo.mock_get_operation(zone.res["name"], operation_id, nlb.res["id"])

        exo.mock_get_v2(
            zone.res["name"],
            "instance-pool/" + instance_pool.id,
            instance_pool.res,
        )
        exo.mock_get_v2(zone.res["name"], "load-balancer/" + nlb.id, nlb.res)

        nlb_service = list(nlb.services)[0]
        nlb_service.update(
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
        assert nlb_service.name == nlb_service_name
        assert nlb_service.description == nlb_service_description
        assert nlb_service.instance_pool.id == instance_pool.res["id"]
        assert nlb_service.port == nlb_service_port
        assert nlb_service.target_port == nlb_service_target_port
        assert nlb_service.protocol == nlb_service_protocol
        assert nlb_service.strategy == nlb_service_strategy
        assert nlb_service.healthcheck.mode == nlb_service_healthcheck_mode
        assert nlb_service.healthcheck.port == nlb_service_healthcheck_port
        assert nlb_service.healthcheck.uri == nlb_service_healthcheck_uri
        assert (
            nlb_service.healthcheck.interval
            == nlb_service_healthcheck_interval
        )
        assert (
            nlb_service.healthcheck.timeout == nlb_service_healthcheck_timeout
        )
        assert (
            nlb_service.healthcheck.retries == nlb_service_healthcheck_retries
        )
        assert (
            nlb_service.healthcheck.tls_sni == nlb_service_healthcheck_tls_sni
        )

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
        instance_pool = InstancePool._from_api(
            exo.compute, instance_pool(), zone=zone
        )
        nlb_service = nlb_service(
            **{"instance-pool": {"id": instance_pool.id}}
        )
        nlb = NetworkLoadBalancer._from_api(
            exo.compute, nlb(services=[nlb_service]), zone=zone
        )
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
            zone.res["name"],
            "load-balancer/{}/service/{}".format(
                nlb.res["id"], nlb_service["id"]
            ),
            _assert_request,
        )
        exo.mock_get_operation(zone.res["name"], operation_id, nlb.res["id"])

        exo.mock_get_v2(
            zone.res["name"],
            "instance-pool/" + instance_pool.id,
            instance_pool.res,
        )
        exo.mock_get_v2(zone.res["name"], "load-balancer/" + nlb.id, nlb.res)

        nlb_service = list(nlb.services)[0]
        nlb_service.delete()
        assert nlb_service.id is None

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
        nlb_service = nlb_service(
            **{"instance-pool": {"id": instance_pool.id}}
        )
        nlb = NetworkLoadBalancer._from_api(
            exo.compute, nlb(services=[nlb_service]), zone=zone
        )

        exo.mock_get_v2(
            zone.res["name"],
            "instance-pool/" + instance_pool.id,
            instance_pool.res,
        )
        exo.mock_get_v2(zone.res["name"], "load-balancer/" + nlb.id, nlb.res)
        exo.mock_get_v2(
            zone.res["name"],
            "load-balancer/{}/service/{}".format(
                nlb.res["id"], nlb_service["id"]
            ),
            nlb_service,
        )

        nlb_service = list(nlb.services)[0]
        assert nlb_service.state == "running"
        assert len(nlb_service.healthcheck_status) > 0
