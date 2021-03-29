#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from .conftest import _random_str, _random_uuid
from exoscale.api.compute import *
from urllib.parse import parse_qs, urlparse


class TestComputePrivateNetwork:
    def test_attach_instance(
        self, exo, zone, privnet, instance_type, instance_template, instance
    ):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        private_network = PrivateNetwork._from_cs(
            exo.compute, privnet(), zone=Zone._from_cs(zone)
        )
        instance = Instance._from_cs(exo.compute, instance(), zone=Zone._from_cs(zone))

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["virtualmachineid"][0] == instance.res["id"]
            assert params["networkid"][0] == private_network.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "addnictovirtualmachineresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=addNicToVirtualMachine", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        private_network.attach_instance(instance)

    def test_detach_instance(
        self, exo, zone, privnet, instance_type, instance_template, instance
    ):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        private_network = PrivateNetwork._from_cs(
            exo.compute, privnet(), zone=Zone._from_cs(zone)
        )
        instance = Instance._from_cs(
            exo.compute,
            instance(private_network_ids=[private_network.res["id"]]),
            zone=Zone._from_cs(zone),
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["virtualmachineid"][0] == instance.res["id"]
            assert params["nicid"][0] == instance.res["nic"][1]["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "removenicfromvirtualmachineresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_list("listNics", [instance.res["nic"][1]])
        exo.mock_get("?command=removeNicFromVirtualMachine", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        private_network.detach_instance(instance)

    def test_update(self, exo, zone, privnet):
        private_network = PrivateNetwork._from_cs(
            exo.compute, privnet(), zone=Zone._from_cs(zone())
        )
        private_network_name = _random_str()
        private_network_description = _random_str()
        private_network_start_ip = "10.0.0.1"
        private_network_end_ip = "10.0.0.100"
        private_network_netmask = "255.255.255.0"

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == private_network.res["id"]
            assert params["name"][0] == private_network_name
            assert params["displaytext"][0] == private_network_description
            assert params["startip"][0] == private_network_start_ip
            assert params["endip"][0] == private_network_end_ip
            assert params["netmask"][0] == private_network_netmask

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "updatenetworkresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=updateNetwork", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        private_network.update(
            name=private_network_name,
            description=private_network_description,
            start_ip=private_network_start_ip,
            end_ip=private_network_end_ip,
            netmask=private_network_netmask,
        )
        assert private_network.name == private_network_name
        assert private_network.description == private_network_description
        assert private_network.start_ip == private_network_start_ip
        assert private_network.end_ip == private_network_end_ip
        assert private_network.netmask == private_network_netmask

    def test_delete(self, exo, zone, privnet):
        private_network = PrivateNetwork._from_cs(
            exo.compute, privnet(), zone=Zone._from_cs(zone())
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == private_network.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "deletenetworkresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=deleteNetwork", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        private_network.delete()
        assert private_network.id is None

    def test_properties(
        self, exo, zone, privnet, instance_type, instance_template, instance
    ):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = Zone._from_cs(zone())
        private_network = PrivateNetwork._from_cs(exo.compute, privnet(), zone=zone)
        instance = Instance._from_cs(
            exo.compute,
            instance(private_network_ids=private_network.res["id"]),
            zone=zone,
        )

        exo.mock_list("listVirtualMachines", [instance.res])

        private_network_instances = list(private_network.instances)
        assert len(private_network_instances) == 1
        assert private_network_instances[0].name == instance.name
