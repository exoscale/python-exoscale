#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from .conftest import _random_str, _random_uuid
from base64 import b64encode
from exoscale.api.compute import *
from urllib.parse import parse_qs, urlparse


class TestComputeInstance:
    def test_update(self, exo, zone, sg, instance_type, instance_template, instance):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        instance = Instance._from_cs(
            exo.compute, instance(), zone=Zone._from_cs(zone())
        )
        instance_name = _random_str()
        instance_user_data = _random_str()
        security_group = SecurityGroup._from_cs(exo.compute, sg())

        def _assert_request_vm(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == instance.res["id"]
            assert params["name"][0] == instance_name

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "updatevirtualmachineresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=updateVirtualMachine", _assert_request_vm)

        def _assert_request_vmsg(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == instance.res["id"]
            assert params["securitygroupids"] == [security_group.res["id"]]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "updatevirtualmachinesecuritygroupsresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get(
            "?command=updateVirtualMachineSecurityGroups", _assert_request_vmsg
        )

        exo.mock_query_async_job_result({"success": True})

        instance.update(name=instance_name, security_groups=[security_group])
        assert instance.name == instance_name

    def test_scale(self, exo, zone, instance_type, instance_template, instance):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        instance = Instance._from_cs(
            exo.compute, instance(type_id=_random_uuid()), zone=Zone._from_cs(zone())
        )
        instance_type = InstanceType._from_cs(instance_type())

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == instance.res["id"]
            assert params["serviceofferingid"][0] == instance_type.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "scalevirtualmachineresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=scaleVirtualMachine", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        instance.scale(type=instance_type)
        assert instance.type.id == instance_type.id

    def test_start(self, exo, zone, instance_type, instance_template, instance):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        instance = Instance._from_cs(
            exo.compute, instance(type_id=_random_uuid()), zone=Zone._from_cs(zone())
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == instance.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "startvirtualmachineresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=startVirtualMachine", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        instance.start()

    def test_stop(self, exo, zone, instance_type, instance_template, instance):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        instance = Instance._from_cs(
            exo.compute, instance(type_id=_random_uuid()), zone=Zone._from_cs(zone())
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == instance.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "stopvirtualmachineresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=stopVirtualMachine", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        instance.stop()

    def test_reboot(self, exo, zone, instance_type, instance_template, instance):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        instance = Instance._from_cs(
            exo.compute, instance(type_id=_random_uuid()), zone=Zone._from_cs(zone())
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == instance.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "rebootvirtualmachineresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=rebootVirtualMachine", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        instance.reboot()

    def test_resize_volume(self, exo, zone, instance_type, instance_template, instance):
        instance_volume = {"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}
        exo.mock_list("listVolumes", [instance_volume])
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        instance = Instance._from_cs(
            exo.compute, instance(type_id=_random_uuid()), zone=Zone._from_cs(zone())
        )
        instance_volume_size = 20
        instance_volume_size_bytes = 20 * 1024 ** 3

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == instance_volume["id"]
            assert params["size"][0] == str(instance_volume_size)

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "resizevolumeresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=resizeVolume", _assert_request)
        exo.mock_query_async_job_result(
            {
                "volume": {
                    **instance_volume,
                    **{"size": instance_volume_size_bytes},
                }
            }
        )

        instance.resize_volume(instance_volume_size)

        res = exo.compute.cs.listVolumes(virtualmachineid=instance.id, fetch_list=True)
        assert instance.volume_size == instance_volume_size_bytes

    def test_snapshot_volume(
        self, exo, zone, instance_type, instance_template, instance, volume_snapshot
    ):
        instance_volume = {"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}
        instance_volume_snapshot = volume_snapshot(volume_id=instance_volume["id"])
        exo.mock_list("listVolumes", [instance_volume])
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        instance = Instance._from_cs(
            exo.compute, instance(type_id=_random_uuid()), zone=Zone._from_cs(zone())
        )
        instance_volume_size = 20

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["volumeid"][0] == instance_volume["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "createsnapshotresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=createSnapshot", _assert_request)
        exo.mock_query_async_job_result({"snapshot": instance_volume_snapshot})

        snapshot = instance.snapshot_volume()
        assert snapshot.id == instance_volume_snapshot["id"]

    def test_attach_elastic_ip(
        self, exo, zone, eip, instance_type, instance_template, instance
    ):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        elastic_ip = ElasticIP._from_cs(exo.compute, eip(), zone=Zone._from_cs(zone))
        instance = Instance._from_cs(exo.compute, instance(), zone=Zone._from_cs(zone))

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["nicid"][0] == instance.res["nic"][0]["id"]
            assert params["ipaddress"][0] == elastic_ip.res["ipaddress"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "addiptonicresponse": {"id": _random_uuid(), "jobid": _random_uuid()}
            }

        exo.mock_list("listNics", [instance.res["nic"][0]])
        exo.mock_get("?command=addIpToNic", _assert_request)
        exo.mock_query_async_job_result({"secondaryip": [instance.res["nic"][0]]})

        instance.attach_elastic_ip(elastic_ip=elastic_ip)

    def test_detach_elastic_ip(
        self, exo, zone, eip, instance_type, instance_template, instance
    ):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        elastic_ip = ElasticIP._from_cs(exo.compute, eip(), zone=Zone._from_cs(zone))
        instance = Instance._from_cs(exo.compute, instance(), zone=Zone._from_cs(zone))
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
        exo.mock_query_async_job_result({"secondaryip": [instance.res["nic"][0]]})

        instance.detach_elastic_ip(elastic_ip)

    def test_attach_private_network(
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

        instance.attach_private_network(private_network=private_network)

    def test_detach_private_network(
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

        instance.detach_private_network(private_network=private_network)

    def test_set_reverse_dns(
        self, exo, zone, instance_type, instance_template, instance
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
        instance_reverse_dns = _random_str()

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == instance.res["id"]
            assert params["domainname"][0] == instance_reverse_dns

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "updatereversednsforvirtualmachineresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=updateReverseDnsForVirtualMachine", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        instance.set_reverse_dns(record=instance_reverse_dns)

    def test_unset_reverse_dns(
        self, exo, zone, instance_type, instance_template, instance
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

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == instance.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "deletereversednsforvirtualmachineresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=deleteReverseDnsFromVirtualMachine", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        instance.unset_reverse_dns()

    def test_delete(self, exo, zone, instance_type, instance_template, instance):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        instance = Instance._from_cs(
            exo.compute, instance(), zone=Zone._from_cs(zone())
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == instance.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "destroyvirtualmachineresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=destroyVirtualMachine", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        instance.delete()
        assert instance.id is None

    def test_properties(
        self,
        exo,
        zone,
        aag,
        sg,
        privnet,
        eip,
        volume_snapshot,
        instance_type,
        instance_template,
        instance,
    ):
        instance_volume = {"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}
        exo.mock_list("listVolumes", [instance_volume])
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = Zone._from_cs(zone())
        anti_affinity_group = AntiAffinityGroup._from_cs(exo.compute, aag())
        private_network = PrivateNetwork._from_cs(exo.compute, privnet(), zone=zone)
        security_group = SecurityGroup._from_cs(exo.compute, sg())
        instance_user_data = _random_str()
        instance_reverse_dns = _random_str()

        instance = Instance._from_cs(
            exo.compute,
            instance(
                security_group_ids=[security_group.res["id"]],
                anti_affinity_group_ids=[anti_affinity_group.res["id"]],
                private_network_ids=[private_network.res["id"]],
                reverse_dns=instance_reverse_dns,
            ),
            zone=zone,
        )

        snapshot = InstanceVolumeSnapshot._from_cs(
            exo.compute, volume_snapshot(volume_id=instance_volume["id"])
        )

        elastic_ip = ElasticIP._from_cs(exo.compute, eip(), zone=zone)
        instance.res["nic"][0]["secondaryip"] = [elastic_ip.res]

        exo.mock_list("listVirtualMachines", [instance.res])
        exo.mock_list("listAffinityGroups", [anti_affinity_group.res])
        exo.mock_list("listSecurityGroups", [security_group.res])
        exo.mock_list("listNetworks", [private_network.res])
        exo.mock_list("listNics", instance.res["nic"])
        exo.mock_list("listPublicIpAddresses", [elastic_ip.res])
        exo.mock_list("listSnapshots", [snapshot.res])
        exo.mock_get(
            "?command=queryReverseDnsForVirtualMachine",
            {
                "queryreversednsforvirtualmachineresponse": {
                    "virtualmachine": instance.res
                }
            },
        )
        exo.mock_get(
            "?command=getVirtualMachineUserData",
            {
                "getvirtualmachineuserdataresponse": {
                    "virtualmachineuserdata": {
                        "userdata": b64encode(
                            bytes(instance_user_data, encoding="utf-8")
                        ).decode("ascii")
                    }
                }
            },
        )

        instance_state = instance.state
        assert instance_state == "running"

        instance_anti_affinity_groups = list(instance.anti_affinity_groups)
        assert len(instance_anti_affinity_groups) == 1
        assert instance_anti_affinity_groups[0].id == anti_affinity_group.id

        instance_security_groups = list(instance.security_groups)
        assert len(instance_security_groups) == 1
        assert instance_security_groups[0].id == security_group.id

        instance_private_networks = list(instance.private_networks)
        assert len(instance_private_networks) == 1
        assert instance_private_networks[0].id == private_network.id

        instance_elastic_ips = list(instance.elastic_ips)
        assert len(instance_elastic_ips) == 1
        assert instance_elastic_ips[0].id == elastic_ip.id

        assert instance.reverse_dns == instance_reverse_dns

        instance_volume_snapshots = list(instance.volume_snapshots)
        assert len(instance_volume_snapshots) == 1
        assert instance_volume_snapshots[0].id == snapshot.id

        assert instance.user_data == instance_user_data
