#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.compute import *
from exoscale.api import ResourceNotFoundError
from .conftest import _random_str


class TestComputeNetworkLoadBalancer:
    def test_add_service(
        self, exo, zone, instance_pool, nlb, test_prefix, test_description
    ):
        zone = Zone._from_cs(zone("ch-gva-2"))
        instance_pool = InstancePool._from_cs(
            exo.compute, instance_pool(zone_id=zone.id)
        )
        nlb = NetworkLoadBalancer._from_api(exo.compute, nlb(), zone)
        service_name = "-".join([test_prefix, _random_str()])
        service_description = test_description
        service_port = 443
        service_target_port = 8443
        service_protocol = "tcp"
        service_strategy = "source-hash"
        service_healthcheck_mode = "https"
        service_healthcheck_port = 8444
        service_healthcheck_uri = "/health"
        service_healthcheck_interval = 5
        service_healthcheck_timeout = 3
        service_healthcheck_retries = 1
        service_healthcheck_tls_sni = "example.net"

        service = nlb.add_service(
            name=service_name,
            description=service_description,
            instance_pool=instance_pool,
            port=service_port,
            target_port=service_target_port,
            protocol=service_protocol,
            strategy=service_strategy,
            healthcheck_mode=service_healthcheck_mode,
            healthcheck_port=service_healthcheck_port,
            healthcheck_uri=service_healthcheck_uri,
            healthcheck_interval=service_healthcheck_interval,
            healthcheck_timeout=service_healthcheck_timeout,
            healthcheck_retries=service_healthcheck_retries,
            healthcheck_tls_sni=service_healthcheck_tls_sni,
        )

        actual_service = exo.compute._v2_request(
            "GET",
            "/load-balancer/{}/service/{}".format(nlb.id, service.id),
            zone=zone.name,
        )

        assert service.id == actual_service["id"]
        assert service.name == service_name
        assert actual_service["name"] == service_name
        assert service.description == test_description
        assert actual_service["description"] == test_description
        assert service.instance_pool.id == instance_pool.id
        assert actual_service["instance-pool"]["id"] == instance_pool.id
        assert service.port == service_port
        assert actual_service["port"] == service_port
        assert service.target_port == service_target_port
        assert actual_service["target-port"] == service_target_port
        assert service.protocol == service_protocol
        assert actual_service["protocol"] == service_protocol
        assert service.strategy == service_strategy
        assert actual_service["strategy"] == service_strategy
        assert service.healthcheck.mode == service_healthcheck_mode
        assert actual_service["healthcheck"]["mode"] == service_healthcheck_mode
        assert service.healthcheck.port == service_healthcheck_port
        assert actual_service["healthcheck"]["port"] == service_healthcheck_port
        assert service.healthcheck.uri == service_healthcheck_uri
        assert actual_service["healthcheck"]["uri"] == service_healthcheck_uri
        assert service.healthcheck.interval == service_healthcheck_interval
        assert actual_service["healthcheck"]["interval"] == service_healthcheck_interval
        assert service.healthcheck.timeout == service_healthcheck_timeout
        assert actual_service["healthcheck"]["timeout"] == service_healthcheck_timeout
        assert service.healthcheck.retries == service_healthcheck_retries
        assert actual_service["healthcheck"]["retries"] == service_healthcheck_retries
        assert service.healthcheck.tls_sni == service_healthcheck_tls_sni
        assert actual_service["healthcheck"]["tls-sni"] == service_healthcheck_tls_sni

    def test_update(self, exo, zone, nlb):
        zone = Zone._from_cs(zone("ch-gva-2"))
        nlb = NetworkLoadBalancer._from_api(exo.compute, nlb(), zone)
        name_edited = nlb.name + "-edited"
        description_edited = nlb.description + " (edited)"

        nlb.update(
            name=name_edited,
            description=description_edited,
        )

        res = exo.compute._v2_request("GET", "/load-balancer/" + nlb.id, zone=zone.name)
        assert res["name"] == name_edited
        assert nlb.name == name_edited
        assert res["description"] == description_edited
        assert nlb.description == description_edited

    def test_delete(self, exo, zone, nlb):
        zone = Zone._from_cs(zone("ch-gva-2"))
        nlb = NetworkLoadBalancer._from_api(exo.compute, nlb(teardown=False), zone)
        nlb_id = nlb.id

        nlb.delete()
        assert nlb.id is None

        with pytest.raises(ResourceNotFoundError) as excinfo:
            res = exo.compute._v2_request("GET", "/load-balancer/" + nlb_id, zone.name)
            assert res is None
        assert excinfo.type == ResourceNotFoundError

    def test_properties(self, exo, zone, instance_pool, nlb):
        zone = Zone._from_cs(zone("ch-gva-2"))
        instance_pool = InstancePool._from_cs(
            exo.compute, instance_pool(zone_id=zone.id)
        )
        nlb = NetworkLoadBalancer._from_api(exo.compute, nlb(), zone)

        res = exo.compute._v2_request_async(
            "POST",
            "/load-balancer/{}/service".format(nlb.id),
            zone.name,
            json={
                "name": "test",
                "instance-pool": {"id": instance_pool.id},
                "port": 80,
                "target-port": 80,
                "protocol": "tcp",
                "strategy": "round-robin",
                "healthcheck": {"mode": "tcp", "port": 80, "interval": 10},
            },
        )

        service = NetworkLoadBalancerService._from_api(
            exo.compute,
            exo.compute._v2_request("GET", "/load-balancer/" + nlb.id, zone.name)[
                "services"
            ][0],
            nlb,
        )
        assert service is not None

        nlb_services = list(nlb.services)
        assert len(nlb_services) == 1
        assert nlb_services[0].id == service.id

        nlb_state = nlb.state
        assert nlb_state == "running"
