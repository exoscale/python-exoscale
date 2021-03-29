#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from .conftest import _random_str, _random_uuid
from base64 import b64decode
from datetime import datetime, timezone
from exoscale.api import ResourceNotFoundError
from exoscale.api.compute import *
from urllib.parse import parse_qs, urljoin, urlparse


class TestCompute:
    ### Anti-Affinity Group
    def test_create_anti_affinity_group(self, exo, aag):
        anti_affinity_group_name = _random_str()
        anti_affinity_group_description = _random_str()
        expected = aag(
            name=anti_affinity_group_name,
            description=anti_affinity_group_description,
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["name"][0] == anti_affinity_group_name
            assert params["description"][0] == anti_affinity_group_description

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "createaffinitygroupresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=createAffinityGroup", _assert_request)
        exo.mock_query_async_job_result({"affinitygroup": expected})

        actual = exo.compute.create_anti_affinity_group(
            name=anti_affinity_group_name, description=anti_affinity_group_description
        )
        assert actual.id == expected["id"]
        assert actual.name == expected["name"]
        assert actual.description == expected["description"]

    def test_list_anti_affinity_groups(self, exo, aag):
        expected = aag()

        exo.mock_list("listAffinityGroups", [expected])
        actual = list(exo.compute.list_anti_affinity_groups())
        assert len(actual) == 1
        assert actual[0].id == expected["id"]

    def test_get_anti_affinity_group(self, exo, aag):
        expected = aag()

        exo.mock_get(
            "?command=listAffinityGroups&id={}".format(expected["id"]),
            {"listaffinitygroupsresponse": {"count": 1, "affinitygroup": [expected]}},
        )
        actual = exo.compute.get_anti_affinity_group(id=expected["id"])
        assert actual.id == expected["id"]

        exo.mock_get(
            "?command=listAffinityGroups&name={}".format(expected["name"]),
            {"listaffinitygroupsresponse": {"count": 1, "affinitygroup": [expected]}},
        )
        actual = exo.compute.get_anti_affinity_group(name=expected["name"])
        assert actual.id == expected["id"]

        with pytest.raises(ResourceNotFoundError) as excinfo:
            exo.mock_get(
                "?command=listAffinityGroups&id=lolnope",
                {"listaffinitygroupsresponse": {}},
            )
            actual = exo.compute.get_anti_affinity_group(id="lolnope")
            assert actual is None
        assert excinfo.type == ResourceNotFoundError

    ### Elastic IP

    def test_create_elastic_ip(self, exo, zone, eip):
        zone = Zone._from_cs(zone())
        elastic_ip_description = _random_str()
        elastic_ip_healthcheck = {
            "mode": "https",
            "port": 443,
            "path": "/health",
            "interval": 5,
            "strikes-ok": 3,
            "strikes-fail": 1,
            "timeout": 3,
            "tls-sni": "example.net",
            "tls-skip-verify": True,
        }
        expected = eip(
            zone_id=zone.id,
            description=elastic_ip_description,
            healthcheck=elastic_ip_healthcheck,
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["zoneid"][0] == expected["zoneid"]
            assert params["description"][0] == elastic_ip_description
            assert params["mode"][0] == expected["healthcheck"]["mode"]
            assert params["port"][0] == str(expected["healthcheck"]["port"])
            assert params["path"][0] == str(expected["healthcheck"]["path"])
            assert params["interval"][0] == str(expected["healthcheck"]["interval"])
            assert params["strikes-ok"][0] == str(expected["healthcheck"]["strikes-ok"])
            assert params["strikes-fail"][0] == str(
                expected["healthcheck"]["strikes-fail"]
            )
            assert params["timeout"][0] == str(expected["healthcheck"]["timeout"])
            assert params["tls-sni"][0] == expected["healthcheck"]["tls-sni"]
            assert params["tls-skip-verify"][0] == str(
                expected["healthcheck"]["tls-skip-verify"]
            )

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "associateipaddressresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=associateIpAddress", _assert_request)
        exo.mock_query_async_job_result({"ipaddress": expected})

        actual = exo.compute.create_elastic_ip(
            zone=zone,
            description=elastic_ip_description,
            healthcheck_mode=expected["healthcheck"]["mode"],
            healthcheck_port=expected["healthcheck"]["port"],
            healthcheck_path=expected["healthcheck"]["path"],
            healthcheck_interval=expected["healthcheck"]["interval"],
            healthcheck_timeout=expected["healthcheck"]["timeout"],
            healthcheck_strikes_ok=expected["healthcheck"]["strikes-ok"],
            healthcheck_strikes_fail=expected["healthcheck"]["strikes-fail"],
            healthcheck_tls_sni=expected["healthcheck"]["tls-sni"],
            healthcheck_tls_skip_verify=expected["healthcheck"]["tls-skip-verify"],
        )
        assert actual.zone == zone
        assert actual.address == expected["ipaddress"]
        assert actual.description == expected["description"]
        assert actual.healthcheck_mode == expected["healthcheck"]["mode"]
        assert actual.healthcheck_port == expected["healthcheck"]["port"]
        assert actual.healthcheck_path == expected["healthcheck"]["path"]
        assert actual.healthcheck_interval == expected["healthcheck"]["interval"]
        assert actual.healthcheck_timeout == expected["healthcheck"]["timeout"]
        assert actual.healthcheck_strikes_ok == expected["healthcheck"]["strikes-ok"]
        assert (
            actual.healthcheck_strikes_fail == expected["healthcheck"]["strikes-fail"]
        )
        assert actual.healthcheck_tls_sni == expected["healthcheck"]["tls-sni"]
        assert (
            actual.healthcheck_tls_skip_verify
            == expected["healthcheck"]["tls-skip-verify"]
        )

    def test_list_elastic_ips(self, exo, zone, eip):
        zone = Zone._from_cs(zone())
        expected = eip()

        exo.mock_list("listPublicIpAddresses", [expected])
        actual = list(exo.compute.list_elastic_ips(zone=zone))
        assert len(actual) == 1
        assert actual[0].id == expected["id"]

    def test_get_elastic_ip(self, exo, zone, eip):
        zone = Zone._from_cs(zone())
        expected = eip()

        exo.mock_get(
            "?command=listPublicIpAddresses&id={}".format(expected["id"]),
            {"listpublicipaddressesresponse": {"count": 1, "ipaddress": [expected]}},
        )
        actual = exo.compute.get_elastic_ip(zone, id=expected["id"])
        assert actual.id == expected["id"]

        exo.mock_get(
            "?command=listPublicIpAddresses&ipaddress={}".format(expected["ipaddress"]),
            {"listpublicipaddressesresponse": {"count": 1, "ipaddress": [expected]}},
        )
        actual = exo.compute.get_elastic_ip(zone, address=expected["ipaddress"])
        assert actual.id == expected["id"]

        with pytest.raises(ResourceNotFoundError) as excinfo:
            exo.mock_get(
                "?command=listPublicIpAddresses&id=lolnope",
                {"listpublicipaddressesresponse": {}},
            )
            actual = exo.compute.get_elastic_ip(zone, id="lolnope")
            assert actual is None
        assert excinfo.type == ResourceNotFoundError

    ### Instance

    def test_create_instance(
        self,
        exo,
        zone,
        aag,
        sg,
        privnet,
        sshkey,
        instance_type,
        instance_template,
        instance,
    ):
        zone = zone()
        instance_type = instance_type()
        instance_template = instance_template()
        anti_affinity_group = aag()
        private_network = privnet()
        security_group = sg()
        ssh_key = sshkey()
        instance_name = _random_str()
        instance_volume_size = 20
        instance_volume_size_bytes = instance_volume_size * 1024 ** 3
        instance_creation_date = datetime.now(tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S+0000"
        )

        expected = instance(
            zone_id=zone["id"],
            name=instance_name,
            created=instance_creation_date,
            type_id=instance_type["id"],
            template_id=instance_template["id"],
            security_group_ids=[security_group["id"]],
            anti_affinity_group_ids=[anti_affinity_group["id"]],
            private_network_ids=[private_network["id"]],
            keypair=ssh_key["name"],
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["zoneid"][0] == expected["zoneid"]
            assert params["name"][0] == expected["name"]
            assert params["templateid"][0] == expected["templateid"]
            assert params["serviceofferingid"][0] == expected["serviceofferingid"]
            assert params["securitygroupids"] == [security_group["id"]]
            assert params["affinitygroupids"] == [anti_affinity_group["id"]]
            assert params["networkids"] == [private_network["id"]]
            assert params["keypair"][0] == expected["keypair"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "deployvirtualmachineresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=deployVirtualMachine", _assert_request)
        exo.mock_query_async_job_result({"virtualmachine": expected})

        exo.mock_list(
            "listVolumes",
            [
                {
                    "id": _random_uuid(),
                    "type": "ROOT",
                    "size": instance_volume_size_bytes,
                }
            ],
        )
        exo.mock_list("listServiceOfferings", [instance_type])
        exo.mock_list("listTemplates", [instance_template])
        exo.mock_list("listSSHKeyPairs", [ssh_key])

        actual = exo.compute.create_instance(
            zone=Zone._from_cs(zone),
            name=instance_name,
            type=InstanceType._from_cs(instance_type),
            template=InstanceTemplate._from_cs(exo.compute, instance_template, zone),
            volume_size=20,
            security_groups=[SecurityGroup._from_cs(exo.compute, security_group)],
            anti_affinity_groups=[
                AntiAffinityGroup._from_cs(exo.compute, anti_affinity_group)
            ],
            private_networks=[
                PrivateNetwork._from_cs(exo.compute, private_network, zone)
            ],
            enable_ipv6=True,
            ssh_key=SSHKey._from_cs(exo.compute, ssh_key),
        )
        assert actual.zone.id == zone["id"]
        assert actual.id == expected["id"]
        assert actual.name == expected["name"]
        assert (
            actual.creation_date.strftime("%Y-%m-%dT%H:%M:%S+0000")
            == instance_creation_date
        )
        assert actual.type.id == instance_type["id"]
        assert actual.template.id == instance_template["id"]
        assert actual.volume_size == instance_volume_size_bytes
        assert actual.ipv4_address == expected["nic"][0]["ipaddress"]
        assert actual.ipv6_address == expected["nic"][0]["ip6address"]
        assert actual.ssh_key.name == ssh_key["name"]

    def test_list_instances(
        self,
        exo,
        zone,
        instance_type,
        instance_template,
        privnet,
        instance,
    ):
        zone = Zone._from_cs(zone())
        expected = instance()

        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])
        exo.mock_list("listVirtualMachines", [expected])

        actual = list(exo.compute.list_instances(zone=zone))
        assert len(actual) == 1
        assert actual[0].id == expected["id"]

    def test_get_instance(self, exo, zone, instance_type, instance_template, instance):
        zone = Zone._from_cs(zone())
        expected = instance()

        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        exo.mock_get(
            "?command=listVirtualMachines&id={}".format(expected["id"]),
            {"listvirtualmachinesresponse": {"count": 1, "virtualmachine": [expected]}},
        )
        actual = exo.compute.get_instance(zone=zone, id=expected["id"])
        assert actual.id == expected["id"]

        exo.mock_get(
            "?command=listVirtualMachines&ipaddress={}".format(
                expected["nic"][0]["ipaddress"]
            ),
            {"listvirtualmachinesresponse": {"count": 1, "virtualmachine": [expected]}},
        )
        actual = exo.compute.get_instance(
            zone=zone, ip_address=expected["nic"][0]["ipaddress"]
        )
        assert actual.id == expected["id"]

        with pytest.raises(ResourceNotFoundError) as excinfo:
            exo.mock_get(
                "?command=listVirtualMachines&id=lolnope",
                {"listvirtualmachinesresponse": {}},
            )

            actual = exo.compute.get_instance(zone=zone, id="lolnope")
            assert actual is None
        assert excinfo.type == ResourceNotFoundError

    ### Instance Template

    def test_register_instance_template(self, exo, zone, instance_template):
        zone = Zone._from_cs(zone())
        expected = instance_template(
            zone_id=zone.res["id"],
            displaytext=_random_str(),
            details={"username": _random_str()},
        )
        url = _random_str()
        boot_mode = "uefi"

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["zoneid"][0] == zone.res["id"]
            assert params["name"][0] == expected["name"]
            assert params["displaytext"][0] == expected["displaytext"]
            assert params["url"][0] == url
            assert params["checksum"][0] == expected["checksum"]
            assert params["bootmode"][0] == boot_mode
            assert params["details[0].username"][0] == expected["details"]["username"]
            assert params["sshkeyenabled"][0] == str(expected["sshkeyenabled"])
            assert params["passwordenabled"][0] == str(expected["passwordenabled"])

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "registercustomtemplateresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=registerCustomTemplate", _assert_request)
        exo.mock_query_async_job_result({"template": [expected]})

        actual = exo.compute.register_instance_template(
            zone=zone,
            url=url,
            checksum=expected["checksum"],
            name=expected["name"],
            description=expected["displaytext"],
            bootmode=boot_mode,
            username=expected["details"]["username"],
            disable_ssh_key=not expected["sshkeyenabled"],
            disable_password_reset=not expected["passwordenabled"],
        )
        assert actual.zone.id == zone.res["id"]
        assert actual.id == expected["id"]
        assert actual.name == expected["name"]
        assert actual.description == expected["displaytext"]
        assert actual.size == expected["size"]
        assert actual.boot_mode == expected["bootmode"]
        assert actual.username == expected["details"]["username"]
        assert actual.ssh_key_enabled == expected["sshkeyenabled"]
        assert actual.password_reset_enabled == expected["sshkeyenabled"]

    def test_list_instance_templates(self, exo, zone, instance_template):
        zone = Zone._from_cs(zone())
        expected = instance_template()

        exo.mock_list("listTemplates", [expected])
        actual = list(exo.compute.list_instance_templates(zone))
        assert len(actual) == 1
        assert actual[0].id == expected["id"]

    def test_get_instance_template(self, exo, zone, instance_template):
        zone = Zone._from_cs(zone())
        expected = instance_template()

        exo.mock_get(
            "?command=listTemplates&id={}".format(expected["id"]),
            {"listtemplatesresponse": {"count": 1, "template": [expected]}},
        )
        actual = exo.compute.get_instance_template(zone, id=expected["id"])
        assert actual.id == expected["id"]

        with pytest.raises(ResourceNotFoundError) as excinfo:
            exo.mock_get(
                "?command=listTemplates&id=lolnope", {"listtemplatesresponse": {}}
            )
            actual = exo.compute.get_instance_template(zone, id="lolnope")
            assert actual is None
        assert excinfo.type == ResourceNotFoundError

    ### Instance Type

    def test_list_instance_types(self, exo, instance_type):
        expected = instance_type()

        exo.mock_list("listServiceOfferings", [expected])
        actual = list(exo.compute.list_instance_types())
        assert len(actual) == 1
        assert actual[0].id == expected["id"]

    def test_get_instance_type(self, exo, instance_type):
        expected = instance_type()

        exo.mock_get(
            "?command=listServiceOfferings&name={}".format(expected["name"]),
            {
                "listserviceofferingsresponse": {
                    "count": 1,
                    "serviceoffering": [expected],
                }
            },
        )
        actual = exo.compute.get_instance_type(name=expected["name"])
        assert actual.id == expected["id"]

        exo.mock_get(
            "?command=listServiceOfferings&id={}".format(expected["id"]),
            {
                "listserviceofferingsresponse": {
                    "count": 1,
                    "serviceoffering": [expected],
                }
            },
        )
        actual = exo.compute.get_instance_type(id=expected["id"])
        assert actual.id == expected["id"]

        with pytest.raises(ResourceNotFoundError) as excinfo:
            exo.mock_get(
                "?command=listServiceOfferings&name=lolnope",
                {"listserviceofferingsresponse": {}},
            )
            actual = exo.compute.get_instance_type(name="lolnope")
            assert actual is None
        assert excinfo.type == ResourceNotFoundError

    ### Instance Pool

    def test_create_instance_pool(
        self,
        exo,
        zone,
        aag,
        sg,
        privnet,
        sshkey,
        instance_type,
        instance_template,
        instance_pool,
    ):
        zone = zone()
        instance_type = instance_type()
        instance_template = instance_template()
        anti_affinity_group = aag()
        private_network = privnet()
        security_group = sg()
        ssh_key = sshkey()
        instance_pool_name = _random_str()
        instance_pool_description = _random_str()
        instance_pool_size = 1
        instances_volume_size = 20
        instance_pool_creation_date = datetime.now(tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S+0000"
        )
        instance_pool_userdata = _random_str()

        expected = instance_pool(
            zone_id=zone["id"],
            name=instance_pool_name,
            description=instance_pool_description,
            created=instance_pool_creation_date,
            type_id=instance_type["id"],
            template_id=instance_template["id"],
            rootdisksize=instances_volume_size,
            security_group_ids=[security_group["id"]],
            anti_affinity_group_ids=[anti_affinity_group["id"]],
            private_network_ids=[private_network["id"]],
            keypair=ssh_key["name"],
            userdata=instance_pool_userdata,
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["zoneid"][0] == expected["zoneid"]
            assert params["name"][0] == instance_pool_name
            assert params["size"][0] == str(expected["size"])
            assert params["templateid"][0] == expected["templateid"]
            assert params["serviceofferingid"][0] == expected["serviceofferingid"]
            assert params["securitygroupids"] == [security_group["id"]]
            assert params["affinitygroupids"] == [anti_affinity_group["id"]]
            assert params["networkids"] == [private_network["id"]]
            assert params["keypair"][0] == expected["keypair"]
            assert (
                b64decode(params["userdata"][0]).decode("utf-8") == expected["userdata"]
            )

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "createinstancepoolresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=createInstancePool", _assert_request)
        exo.mock_query_async_job_result(expected)
        exo.mock_list("listServiceOfferings", [instance_type])
        exo.mock_list("listTemplates", [instance_template])

        actual = exo.compute.create_instance_pool(
            zone=Zone._from_cs(zone),
            name=instance_pool_name,
            size=instance_pool_size,
            description=instance_pool_description,
            instance_type=InstanceType._from_cs(instance_type),
            instance_template=InstanceTemplate._from_cs(
                exo.compute, instance_template, Zone._from_cs(zone)
            ),
            instance_volume_size=instances_volume_size,
            instance_security_groups=[
                SecurityGroup._from_cs(exo.compute, security_group)
            ],
            instance_anti_affinity_groups=[
                AntiAffinityGroup._from_cs(exo.compute, anti_affinity_group)
            ],
            instance_private_networks=[
                PrivateNetwork._from_cs(
                    exo.compute, private_network, Zone._from_cs(zone)
                )
            ],
            instance_ssh_key=SSHKey._from_cs(exo.compute, ssh_key),
            instance_user_data=instance_pool_userdata,
        )
        assert actual.zone.id == zone["id"]
        assert actual.id == expected["id"]
        assert actual.name == instance_pool_name
        assert actual.description == instance_pool_description
        assert actual.size == instance_pool_size
        assert actual.instance_type.id == instance_type["id"]
        assert actual.instance_template.id == instance_template["id"]
        assert actual.instance_volume_size == instances_volume_size
        assert actual.instance_user_data == instance_pool_userdata

    def test_list_instance_pools(
        self, exo, zone, instance_type, instance_template, instance_pool
    ):
        zone = zone()
        expected = instance_pool()

        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        exo.mock_list("listInstancePools", [expected])
        actual = list(exo.compute.list_instance_pools(zone=Zone._from_cs(zone)))
        assert len(actual) == 1
        assert actual[0].id == expected["id"]

    def test_get_instance_pool(
        self, exo, zone, instance_type, instance_template, instance_pool
    ):
        zone = zone()
        expected = instance_pool()

        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        exo.mock_get(
            "?command=getInstancePool&id={}".format(expected["id"]),
            {"listinstancepoolsresponse": {"count": 1, "instancepool": [expected]}},
        )
        actual = exo.compute.get_instance_pool(Zone._from_cs(zone), id=expected["id"])
        assert actual.id == expected["id"]

        with pytest.raises(ResourceNotFoundError) as excinfo:
            exo.mocker.get(
                urljoin(exo.compute.endpoint, "?command=getInstancePool&id=lolnope"),
                status_code=404,
                json={"errorresponse": {"errortext": "entity does not exist"}},
                headers={"Content-Type": "application/json"},
            )
            actual = exo.compute.get_instance_pool(Zone._from_cs(zone), id="lolnope")
        assert excinfo.type == ResourceNotFoundError

    ### Network Load Balancer

    def test_create_network_load_balancer(self, exo, zone, nlb):
        zone = zone()
        nlb_name = _random_str()
        nlb_description = _random_str()
        nlb_creation_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        operation_id = _random_uuid()

        expected = nlb(
            zone=zone["name"],
            name=nlb_name,
            description=nlb_description,
            created=nlb_creation_date,
        )

        def _assert_request(request, context):
            body = json.loads(request.body)
            assert body["name"] == nlb_name
            assert body["description"] == nlb_description

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "id": operation_id,
                "state": "success",
                "reference": {"id": expected["id"]},
            }

        exo.mock_post(zone["name"], "load-balancer", _assert_request)
        exo.mock_get_operation(zone["name"], operation_id, expected["id"])
        exo.mock_get_v2(zone["name"], "load-balancer", {"load-balancers": [expected]})
        actual = exo.compute.create_network_load_balancer(
            zone=Zone._from_cs(zone),
            name=nlb_name,
            description=nlb_description,
        )
        assert actual.zone.name == zone["name"]
        assert actual.name == expected["name"]
        assert actual.description == expected["description"]
        assert actual.creation_date.strftime("%Y-%m-%dT%H:%M:%SZ") == nlb_creation_date
        assert actual.ip_address == expected["ip"]

    def test_list_network_load_balancers(self, exo, zone, nlb):
        zone = zone()
        expected = nlb(zone=zone["name"])

        exo.mock_get_v2(zone["name"], "load-balancer", {"load-balancers": [expected]})
        actual = list(exo.compute.list_network_load_balancers(zone=Zone._from_cs(zone)))
        assert len(actual) == 1
        assert actual[0].id == expected["id"]

    def test_get_network_load_balancer(self, exo, zone, nlb):
        zone = zone()
        expected = nlb(zone=zone["name"])

        exo.mock_get_v2(zone["name"], "load-balancer", {"load-balancers": [expected]})
        actual = exo.compute.get_network_load_balancer(
            zone=Zone._from_cs(zone), id=expected["id"]
        )
        assert actual.id == expected["id"]

        actual = exo.compute.get_network_load_balancer(
            zone=Zone._from_cs(zone), name=expected["name"]
        )
        assert actual.id == expected["id"]

        with pytest.raises(ResourceNotFoundError) as excinfo:
            actual = exo.compute.get_network_load_balancer(
                zone=Zone._from_cs(zone), id="lolnope"
            )
            assert actual is None
        assert excinfo.type == ResourceNotFoundError

    ### Private Network

    def test_create_private_network(self, exo, zone, privnet):
        zone = zone()
        private_network_name = _random_str()
        private_network_description = _random_str()
        private_network_start_ip = "192.168.1.10"
        private_network_end_ip = "192.168.1.100"
        private_network_netmask = "255.255.255.0"

        expected = privnet(
            zone_id=zone["id"],
            description=private_network_description,
            startip=private_network_start_ip,
            endip=private_network_end_ip,
            netmask=private_network_netmask,
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["zoneid"][0] == zone["id"]
            assert params["name"][0] == private_network_name
            assert params["displaytext"][0] == private_network_description
            assert params["startip"][0] == private_network_start_ip
            assert params["endip"][0] == private_network_end_ip
            assert params["netmask"][0] == private_network_netmask

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "createnetworkresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=createNetwork", _assert_request)
        exo.mock_query_async_job_result({"network": expected})
        actual = exo.compute.create_private_network(
            zone=Zone._from_cs(zone),
            name=private_network_name,
            description=private_network_description,
            start_ip=private_network_start_ip,
            end_ip=private_network_end_ip,
            netmask=private_network_netmask,
        )
        assert actual.zone.id == zone["id"]
        assert actual.name == expected["name"]
        assert actual.description == expected["displaytext"]
        assert actual.start_ip == expected["startip"]
        assert actual.end_ip == expected["endip"]
        assert actual.netmask == expected["netmask"]

    def test_list_private_networks(self, exo, zone, privnet):
        zone = zone()
        expected = privnet()

        exo.mock_list("listNetworks", [expected])
        actual = list(exo.compute.list_private_networks(zone=Zone._from_cs(zone)))
        assert len(actual) == 1
        assert actual[0].id == expected["id"]

    def test_get_private_network(self, exo, zone, privnet):
        zone = zone()
        expected = privnet()

        exo.mock_get(
            "?command=listNetworks&id={}".format(expected["id"]),
            {"listnetworksresponse": {"count": 1, "network": [expected]}},
        )
        actual = exo.compute.get_private_network(Zone._from_cs(zone), id=expected["id"])
        assert actual.id == expected["id"]

        with pytest.raises(ResourceNotFoundError) as excinfo:
            exo.mock_get(
                "?command=listNetworks&id=lolnope", {"listnetworksresponse": {}}
            )
            actual = exo.compute.get_private_network(Zone._from_cs(zone), id="lolnope")
            assert actual is None
        assert excinfo.type == ResourceNotFoundError

    ### Security Group

    def test_create_security_group(self, exo, sg):
        security_group_name = _random_str()
        security_group_description = _random_str()
        expected = sg(
            name=security_group_name,
            description=security_group_description,
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["name"][0] == security_group_name
            assert params["description"][0] == security_group_description

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "createsecuritygroupresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=createSecurityGroup", _assert_request)
        exo.mock_query_async_job_result({"securitygroup": expected})
        actual = exo.compute.create_security_group(
            name=security_group_name, description=security_group_description
        )
        assert actual.id == expected["id"]
        assert actual.name == expected["name"]
        assert actual.description == expected["description"]

    def test_list_security_groups(self, exo, sg):
        expected = sg()

        exo.mock_list("listSecurityGroups", [expected])
        actual = list(exo.compute.list_security_groups())
        assert len(actual) == 1
        assert actual[0].id == expected["id"]

    def test_get_security_group(self, exo, sg):
        expected = sg()

        exo.mock_get(
            "?command=listSecurityGroups&id={}".format(expected["id"]),
            {"listsecuritygroupsresponse": {"count": 1, "securitygroups": [expected]}},
        )
        actual = exo.compute.get_security_group(id=expected["id"])
        assert actual.id == expected["id"]

        exo.mock_get(
            "?command=listSecurityGroups&securitygroupname={}".format(expected["name"]),
            {"listsecuritygroupsresponse": {"count": 1, "securitygroups": [expected]}},
        )
        actual = exo.compute.get_security_group(name=expected["name"])
        assert actual.id == expected["id"]

        with pytest.raises(ResourceNotFoundError) as excinfo:
            exo.mock_get(
                "?command=listSecurityGroups&id=lolnope",
                {"listsecuritygroupsresponse": {}},
            )
            actual = exo.compute.get_security_group(id="lolnope")
            assert actual is None
        assert excinfo.type == ResourceNotFoundError

    ### SSH Key

    def test_create_ssh_key(self, exo, sshkey):
        ssh_key_name = _random_str()

        expected = sshkey(name=ssh_key_name)

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["name"][0] == ssh_key_name

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {"createsshkeypairresponse": {"keypair": expected}}

        exo.mock_get("?command=createSSHKeyPair", _assert_request)
        actual = exo.compute.create_ssh_key(name=ssh_key_name)
        assert actual.name == expected["name"]
        assert actual.fingerprint == expected["fingerprint"]
        assert actual.private_key == expected["privatekey"]

    def test_register_ssh_key(self, exo, sshkey):
        ssh_key_name = _random_str()
        ssh_key_public_key = (
            "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDGRYWaNYBG/Ld3ZnXGsK9pZl9kT3B6GX"
            + "vsslgy/LCjkJvDIP+nL+opAArKZD1P1+SGylCLt8ISdJNNGLtxKp9CL12EGAYqdDvm5P"
            + "urkpqIkEsfhsIG4dne9hNu7ZW8aHGHDWM62/4uiWOKtbGdv/P33L/FepzypwpivFsaXw"
            + "PYVunAgoBQLUAmj/xcwtx7cvKS4zdj0+Iu21CIGU9wsH3ZLS34QiXtCGJyMOp158qld9"
            + "Oeus3Y/7DQ4w5XvfGn9sddxHOSMwUlNiFVty673X3exgMIc8psZOsHvWZPS0zWx9gEDE"
            + "95cUU10K6u4vzTr2O6fgDOQBynEUw3CDiHvwRD alice@example.net"
        )

        expected = sshkey(name=ssh_key_name)
        expected.pop("privatekey")

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["name"][0] == ssh_key_name

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {"registersshkeypairresponse": {"keypair": expected}}

        exo.mock_get("?command=registerSSHKeyPair", _assert_request)
        actual = exo.compute.register_ssh_key(
            name=ssh_key_name, public_key=ssh_key_public_key
        )
        assert actual.name == expected["name"]
        assert actual.fingerprint == expected["fingerprint"]

    def test_list_ssh_keys(self, exo, sshkey):
        expected = sshkey()

        exo.mock_list("listSSHKeyPairs", [expected])
        actual = list(exo.compute.list_ssh_keys())
        assert len(actual) == 1
        assert actual[0].name == expected["name"]

    def test_get_ssh_key(self, exo, sshkey):
        ssh_key_name = _random_str()
        expected = sshkey(name=ssh_key_name)

        exo.mock_get(
            "?command=listSSHKeyPairs&name={}".format(expected["name"]),
            {"listsshkeypairsresponse": {"count": 1, "sshkeypair": [expected]}},
        )
        actual = exo.compute.get_ssh_key(name=ssh_key_name)
        assert actual.name == expected["name"]

        with pytest.raises(ResourceNotFoundError) as excinfo:
            exo.mock_get(
                "?command=listSSHKeyPairs&name=lolnope", {"listsshkeypairsresponse": {}}
            )

            actual = exo.compute.get_ssh_key(name="lolnope")
            assert actual is None
        assert excinfo.type == ResourceNotFoundError

    ### Zone

    def test_list_zones(self, exo):
        expected_zones = [
            "at-vie-1",
            "bg-sof-1",
            "ch-dk-2",
            "ch-gva-2",
            "de-fra-1",
            "de-muc-1",
        ]

        exo.mock_list(
            "listZones",
            [
                {"id": _random_uuid(), "name": "at-vie-1"},
                {"id": _random_uuid(), "name": "bg-sof-1"},
                {"id": _random_uuid(), "name": "ch-dk-2"},
                {"id": _random_uuid(), "name": "ch-gva-2"},
                {"id": _random_uuid(), "name": "de-fra-1"},
                {"id": _random_uuid(), "name": "de-muc-1"},
            ],
        )

        actual = list(exo.compute.list_zones())
        assert len(actual) == len(expected_zones)

    def test_get_zone(self, exo, zone):
        expected = zone()

        exo.mock_get(
            "?command=listZones&id={}".format(expected["id"]),
            {"listzonesresponse": {"count": 1, "zone": [expected]}},
        )
        actual = exo.compute.get_zone(id=expected["id"])
        assert actual.id == expected["id"]

        exo.mock_get(
            "?command=listZones&name={}".format(expected["name"]),
            {"listzonesresponse": {"count": 1, "zone": [expected]}},
        )
        actual = exo.compute.get_zone(name=expected["name"])
        assert actual.id == expected["id"]

        with pytest.raises(ResourceNotFoundError) as excinfo:
            exo.mock_get(
                "?command=listZones&name=lolnope",
                {"listzonesresponse": {}},
            )
            actual = exo.compute.get_zone(name="lolnope")
            assert actual is None
        assert excinfo.type == ResourceNotFoundError
