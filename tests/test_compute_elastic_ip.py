#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .conftest import _random_str, _random_uuid
from exoscale.api.compute import ElasticIP, Instance, Zone
from urllib.parse import parse_qs, urlparse


class TestComputeElasticIP:
    def test_attach_instance(
        self, exo, zone, eip, instance_type, instance_template, instance
    ):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024**3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        elastic_ip = ElasticIP._from_cs(
            exo.compute, eip(), zone=Zone._from_cs(zone)
        )
        instance = Instance._from_cs(
            exo.compute, instance(), zone=Zone._from_cs(zone)
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["nicid"][0] == instance.res["nic"][0]["id"]
            assert params["ipaddress"][0] == elastic_ip.res["ipaddress"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "addiptonicresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_list("listNics", [instance.res["nic"][0]])
        exo.mock_get("?command=addIpToNic", _assert_request)
        exo.mock_query_async_job_result(
            {"secondaryip": [instance.res["nic"][0]]}
        )

        elastic_ip.attach_instance(instance)

    def test_detach_instance(
        self, exo, zone, eip, instance_type, instance_template, instance
    ):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024**3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        elastic_ip = ElasticIP._from_cs(
            exo.compute, eip(), zone=Zone._from_cs(zone)
        )
        instance = Instance._from_cs(
            exo.compute, instance(), zone=Zone._from_cs(zone)
        )
        instance.res["nic"][0]["secondaryip"] = [elastic_ip.res]

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == elastic_ip.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "removeipfromnicresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_list("listNics", instance.res["nic"])
        exo.mock_get("?command=removeIpFromNic", _assert_request)
        exo.mock_query_async_job_result(
            {"secondaryip": [instance.res["nic"][0]]}
        )

        elastic_ip.detach_instance(instance)

    def test_set_reverse_dns(self, exo, zone, eip):
        elastic_ip = ElasticIP._from_cs(
            exo.compute, eip(), zone=Zone._from_cs(zone())
        )
        elastic_ip_reverse_dns = _random_str()

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == elastic_ip.res["id"]
            assert params["domainname"][0] == elastic_ip_reverse_dns

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "removeipfromnicresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get(
            "?command=updateReverseDnsForPublicIpAddress", _assert_request
        )
        exo.mock_query_async_job_result({"success": True})

        elastic_ip.set_reverse_dns(record=elastic_ip_reverse_dns)

    def test_unset_reverse_dns(self, exo, zone, eip):
        elastic_ip = ElasticIP._from_cs(
            exo.compute, eip(), zone=Zone._from_cs(zone())
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == elastic_ip.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "removeipfromnicresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get(
            "?command=deleteReverseDnsFromPublicIpAddress", _assert_request
        )
        exo.mock_query_async_job_result({"success": True})

        elastic_ip.unset_reverse_dns()

    def test_update(self, exo, zone, eip):
        elastic_ip = ElasticIP._from_cs(
            exo.compute, eip(), zone=Zone._from_cs(zone())
        )
        elastic_ip_description = _random_str()
        elastic_ip_healthcheck_mode = "https"
        elastic_ip_healthcheck_port = 443
        elastic_ip_healthcheck_path = "/test"
        elastic_ip_healthcheck_interval = 5
        elastic_ip_healthcheck_timeout = 3
        elastic_ip_healthcheck_strikes_ok = 2
        elastic_ip_healthcheck_strikes_fail = 1
        elastic_ip_healthcheck_tls_sni = "example.net"
        elastic_ip_healthcheck_tls_skip_verify = True

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == elastic_ip.res["id"]
            assert params["description"][0] == elastic_ip_description
            assert params["mode"][0] == elastic_ip_healthcheck_mode
            assert params["port"][0] == str(elastic_ip_healthcheck_port)
            assert params["path"][0] == str(elastic_ip_healthcheck_path)
            assert params["interval"][0] == str(
                elastic_ip_healthcheck_interval
            )
            assert params["strikes-ok"][0] == str(
                elastic_ip_healthcheck_strikes_ok
            )
            assert params["strikes-fail"][0] == str(
                elastic_ip_healthcheck_strikes_fail
            )
            assert params["timeout"][0] == str(elastic_ip_healthcheck_timeout)
            assert params["tls-sni"][0] == elastic_ip_healthcheck_tls_sni
            assert params["tls-skip-verify"][0] == str(
                elastic_ip_healthcheck_tls_skip_verify
            )

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "removeipfromnicresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=updateIpAddress", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        elastic_ip.update(
            description=elastic_ip_description,
            healthcheck_mode=elastic_ip_healthcheck_mode,
            healthcheck_path=elastic_ip_healthcheck_path,
            healthcheck_port=elastic_ip_healthcheck_port,
            healthcheck_interval=elastic_ip_healthcheck_interval,
            healthcheck_timeout=elastic_ip_healthcheck_timeout,
            healthcheck_strikes_ok=elastic_ip_healthcheck_strikes_ok,
            healthcheck_strikes_fail=elastic_ip_healthcheck_strikes_fail,
            healthcheck_tls_sni=elastic_ip_healthcheck_tls_sni,
            healthcheck_tls_skip_verify=elastic_ip_healthcheck_tls_skip_verify,
        )
        assert elastic_ip.description == elastic_ip_description
        assert elastic_ip.healthcheck_mode == elastic_ip_healthcheck_mode
        assert elastic_ip.healthcheck_port == elastic_ip_healthcheck_port
        assert elastic_ip.healthcheck_path == elastic_ip_healthcheck_path
        assert (
            elastic_ip.healthcheck_interval == elastic_ip_healthcheck_interval
        )
        assert elastic_ip.healthcheck_timeout == elastic_ip_healthcheck_timeout
        assert (
            elastic_ip.healthcheck_strikes_ok
            == elastic_ip_healthcheck_strikes_ok
        )
        assert (
            elastic_ip.healthcheck_strikes_fail
            == elastic_ip_healthcheck_strikes_fail
        )
        assert (
            elastic_ip.healthcheck_tls_skip_verify
            == elastic_ip_healthcheck_tls_skip_verify
        )
        assert elastic_ip.healthcheck_tls_sni == elastic_ip_healthcheck_tls_sni

    def test_delete(self, exo, zone, eip):
        elastic_ip = ElasticIP._from_cs(
            exo.compute, eip(), zone=Zone._from_cs(zone())
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == elastic_ip.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "removeipfromnicresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=disassociateIpAddress", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        elastic_ip.delete()
        assert elastic_ip.id is None

    def test_properties(
        self, exo, zone, eip, instance_type, instance_template, instance
    ):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024**3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        elastic_ip_reverse_dns = _random_str()
        elastic_ip = ElasticIP._from_cs(
            exo.compute,
            eip(reverse_dns=elastic_ip_reverse_dns),
            zone=Zone._from_cs(zone),
        )
        instance = Instance._from_cs(
            exo.compute, instance(), zone=Zone._from_cs(zone)
        )
        instance.res["nic"][0]["secondaryip"] = [elastic_ip.res]

        exo.mock_list("listVirtualMachines", [instance.res])
        exo.mock_get(
            "?command=queryReverseDnsForPublicIpAddress",
            {
                "queryreversednsforpublicipaddressresponse": {
                    "publicipaddress": elastic_ip.res
                }
            },
        )

        elastic_ip_instances = list(elastic_ip.instances)
        assert len(elastic_ip_instances) == 1
        assert elastic_ip_instances[0].name == instance.name
        assert elastic_ip.reverse_dns == elastic_ip_reverse_dns
