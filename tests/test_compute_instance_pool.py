#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from .conftest import _random_str, _random_uuid
from base64 import b64decode
from exoscale.api.compute import *
from urllib.parse import parse_qs, urlparse


class TestComputeInstancePool:
    def test_scale(self, exo, zone, instance_type, instance_template, instance_pool):
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        instance_pool = InstancePool._from_api(
            exo.compute, instance_pool(), zone=Zone._from_cs(zone)
        )
        instance_pool_size = 3
        operation_id = _random_uuid()

        def _assert_request(request, context):
            body = json.loads(request.body)
            assert body["size"] == instance_pool_size

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "id": operation_id,
                "state": "success",
                "reference": {"id": instance_pool.res["id"]},
            }

        exo.mock_put(
            zone["name"],
            "instance-pool/{}:scale".format(instance_pool.res["id"]),
            _assert_request,
        )
        exo.mock_get_operation(zone["name"], operation_id, instance_pool.res["id"])

        instance_pool.scale(instance_pool_size)
        assert instance_pool.size == instance_pool_size

    def test_evict(
        self, exo, zone, instance_type, instance_template, instance, instance_pool
    ):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        instance_pool = InstancePool._from_api(
            exo.compute, instance_pool(size=2), zone=Zone._from_cs(zone)
        )
        instance = Instance._from_cs(exo.compute, instance(), zone=Zone._from_cs(zone))
        operation_id = _random_uuid()

        def _assert_request(request, context):
            body = json.loads(request.body)
            assert body["instances"] == [instance.id]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "id": operation_id,
                "state": "success",
                "reference": {"id": instance_pool.res["id"]},
            }

        exo.mock_put(
            zone["name"],
            "instance-pool/{}:evict".format(instance_pool.res["id"]),
            _assert_request,
        )
        exo.mock_get_operation(zone["name"], operation_id, instance_pool.res["id"])

        instance_pool.evict([instance])
        assert instance_pool.size == 1

    def test_update(
        self,
        exo,
        zone,
        aag,
        sg,
        privnet,
        eip,
        dt,
        sshkey,
        instance_type,
        instance_template,
        instance_pool,
    ):
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        instance_pool = InstancePool._from_api(
            exo.compute, instance_pool(), zone=Zone._from_cs(zone)
        )
        instance_type = instance_type()
        instance_template = instance_template()
        anti_affinity_group = aag()
        private_network = privnet()
        security_group = sg()
        elastic_ip = eip()
        ssh_key = sshkey()
        deploy_target = dt()
        instance_pool_name = _random_str()
        instance_pool_description = _random_str()
        instance_volume_size = instance_pool.instance_volume_size * 2
        instance_prefix = _random_str()
        instance_pool_userdata = _random_str()
        instance_pool_userdata_encoded = b64encode(
            bytes(instance_pool_userdata, encoding="utf-8")
        ).decode("ascii")
        operation_id = _random_uuid()

        def _assert_request(request, context):
            body = json.loads(request.body)
            assert body["anti-affinity-groups"][0]["id"] == anti_affinity_group["id"]
            assert body["deploy-target"]["id"] == deploy_target["id"]
            assert body["description"] == instance_pool_description
            assert body["disk-size"] == instance_volume_size
            assert body["elastic-ips"][0]["id"] == elastic_ip["id"]
            assert body["instance-prefix"] == instance_prefix
            assert body["instance-type"]["id"] == instance_type["id"]
            assert body["ipv6-enabled"] == True
            assert body["name"] == instance_pool_name
            assert body["private-networks"][0]["id"] == private_network["id"]
            assert body["security-groups"][0]["id"] == security_group["id"]
            assert body["ssh-key"] == ssh_key["name"]
            assert body["template"]["id"] == instance_template["id"]
            assert body["user-data"] == instance_pool_userdata_encoded

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "id": operation_id,
                "state": "success",
                "reference": {"id": instance_pool.res["id"]},
            }

        exo.mock_put(zone["name"], "instance-pool/" + instance_pool.id, _assert_request)
        exo.mock_get_operation(zone["name"], operation_id, instance_pool.res["id"])

        instance_pool.update(
            name=instance_pool_name,
            description=instance_pool_description,
            instance_anti_affinity_groups=[
                AntiAffinityGroup._from_cs(exo.compute, anti_affinity_group)
            ],
            instance_deploy_target=DeployTarget._from_api(deploy_target, zone),
            instance_elastic_ips=[
                ElasticIP._from_cs(exo.compute, elastic_ip, Zone._from_cs(zone))
            ],
            instance_enable_ipv6=True,
            instance_prefix=instance_prefix,
            instance_private_networks=[
                PrivateNetwork._from_cs(
                    exo.compute, private_network, Zone._from_cs(zone)
                )
            ],
            instance_security_groups=[
                SecurityGroup._from_cs(exo.compute, security_group)
            ],
            instance_ssh_key=SSHKey._from_cs(exo.compute, ssh_key),
            instance_template=InstanceTemplate._from_cs(
                exo.compute, instance_template, Zone._from_cs(zone)
            ),
            instance_type=InstanceType._from_cs(instance_type),
            instance_user_data=instance_pool_userdata,
            instance_volume_size=instance_volume_size,
        )
        assert instance_pool.name == instance_pool_name
        assert instance_pool.description == instance_pool_description
        assert instance_pool.instance_deploy_target.id == deploy_target["id"]
        assert instance_pool.instance_ipv6_enabled == True
        assert instance_pool.instance_prefix == instance_prefix
        assert instance_pool.instance_ssh_key.name == ssh_key["name"]
        assert instance_pool.instance_template.id == instance_template["id"]
        assert instance_pool.instance_type.id == instance_type["id"]
        assert instance_pool.instance_user_data == instance_pool_userdata_encoded
        assert instance_pool.instance_volume_size == instance_volume_size

    def test_delete(self, exo, zone, instance_type, instance_template, instance_pool):
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        instance_pool = InstancePool._from_api(
            exo.compute, instance_pool(), Zone._from_cs(zone)
        )
        operation_id = _random_uuid()

        def _assert_request(request, context):
            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "id": operation_id,
                "state": "success",
                "reference": {"id": instance_pool.res["id"]},
            }

        exo.mock_delete(
            zone["name"], "instance-pool/" + instance_pool.id, _assert_request
        )
        exo.mock_get_operation(zone["name"], operation_id, instance_pool.res["id"])

        instance_pool.delete()
        assert instance_pool.id is None

    def test_properties(
        self,
        exo,
        zone,
        aag,
        sg,
        privnet,
        eip,
        instance_type,
        instance_template,
        instance,
        instance_pool,
    ):
        exo.mock_list(
            "listVolumes",
            [{"id": _random_uuid(), "type": "ROOT", "size": 10 * 1024 ** 3}],
        )
        exo.mock_list("listServiceOfferings", [instance_type()])
        exo.mock_list("listTemplates", [instance_template()])

        zone = zone()
        anti_affinity_group = aag()
        security_group = sg()
        private_network = privnet()
        elastic_ip = eip()
        instance_pool = InstancePool._from_api(
            exo.compute,
            instance_pool(
                **{
                    "size": 1,
                    "anti-affinity-groups": [{"id": anti_affinity_group["id"]}],
                    "elastic-ips": [{"id": elastic_ip["id"]}],
                    "private-networks": [{"id": private_network["id"]}],
                    "security-groups": [{"id": security_group["id"]}],
                }
            ),
            zone=Zone._from_cs(zone),
        )
        instance = instance(manager="instancepool", managerid=instance_pool.id)

        exo.mock_list("listAffinityGroups", [anti_affinity_group])
        exo.mock_list("listSecurityGroups", [security_group])
        exo.mock_list("listNetworks", [private_network])
        exo.mock_list("listPublicIpAddresses", [elastic_ip])
        exo.mock_list("listVirtualMachines", [instance])
        exo.mock_get_v2(
            zone["name"], "instance-pool/" + instance_pool.id, instance_pool.res
        )

        instance_pool_instances = list(instance_pool.instances)
        assert len(instance_pool_instances) == 1
        assert instance_pool_instances[0].id == instance["id"]

        instance_pool_anti_affinity_groups = list(instance_pool.anti_affinity_groups)
        assert len(instance_pool_anti_affinity_groups) == 1
        assert instance_pool_anti_affinity_groups[0].id == anti_affinity_group["id"]

        instance_pool_security_groups = list(instance_pool.security_groups)
        assert len(instance_pool_security_groups) == 1
        assert instance_pool_security_groups[0].id == security_group["id"]

        instance_pool_private_networks = list(instance_pool.private_networks)
        assert len(instance_pool_private_networks) == 1
        assert instance_pool_private_networks[0].id == private_network["id"]

        instance_pool_elastic_ips = list(instance_pool.elastic_ips)
        assert len(instance_pool_elastic_ips) == 1
        assert instance_pool_elastic_ips[0].id == elastic_ip["id"]

        assert instance_pool.state == "running"
