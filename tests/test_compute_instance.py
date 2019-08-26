#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.compute import *


class TestComputeInstance:
    def test_update(self, exo, instance):
        instance = Instance.from_cs(exo.compute, instance(start=False))
        name_edited = instance.name + "-edited"
        security_group_default = SecurityGroup.from_cs(
            exo.compute,
            exo.compute.cs.listSecurityGroups(
                securitygroupname="default", fetch_list=True
            )[0],
        )

        instance.update(name=name_edited, security_groups=[security_group_default])

        [res] = exo.compute.cs.listVirtualMachines(id=instance.id, fetch_list=True)
        assert res["name"] == name_edited
        assert instance.name == name_edited

        [res] = exo.compute.cs.listSecurityGroups(
            virtualmachineid=instance.id, fetch_list=True
        )
        assert res["id"] == security_group_default.id

    def test_scale(self, exo, instance):
        instance = Instance.from_cs(exo.compute, instance(start=False))
        instance_type_small = InstanceType.from_cs(
            exo.compute.cs.listServiceOfferings(name="small", fetch_list=True)[0]
        )

        instance.scale(type=instance_type_small)

        [res] = exo.compute.cs.listVirtualMachines(id=instance.id, fetch_list=True)
        assert res["serviceofferingid"] == instance_type_small.id

    def test_start(self, exo, instance):
        instance = Instance.from_cs(exo.compute, instance(start=False))

        instance.start()

        [res] = exo.compute.cs.listVirtualMachines(id=instance.id, fetch_list=True)
        assert res["state"].lower() in {"starting", "running"}

    def test_stop(self, exo, instance):
        instance = Instance.from_cs(exo.compute, instance())

        instance.stop()

        [res] = exo.compute.cs.listVirtualMachines(id=instance.id, fetch_list=True)
        assert res["state"].lower() in ["stopping", "stopped"]

    def test_reboot(self, exo, instance):
        instance = Instance.from_cs(exo.compute, instance())

        instance.reboot()

        [res] = exo.compute.cs.listVirtualMachines(id=instance.id, fetch_list=True)
        assert res["state"].lower() in ["starting", "running"]

    def test_attach_elastic_ip(self, exo, eip, instance):
        elastic_ip = ElasticIP.from_cs(exo.compute, eip())
        instance = Instance.from_cs(exo.compute, instance())

        instance.attach_elastic_ip(elastic_ip=elastic_ip)

        res = exo.compute.cs.listNics(virtualmachineid=instance.id, fetch_list=True)
        for nic in res:
            if not nic["isdefault"]:
                continue
            assert nic["secondaryip"][0]["ipaddress"] == elastic_ip.address

    def test_detach_elastic_ip(self, exo, eip, instance):
        elastic_ip = ElasticIP.from_cs(exo.compute, eip())
        instance = Instance.from_cs(exo.compute, instance())

        instance.attach_elastic_ip(elastic_ip=elastic_ip)

        res = exo.compute.cs.listNics(virtualmachineid=instance.id, fetch_list=True)
        for nic in res:
            if not nic["isdefault"]:
                continue
            assert nic["secondaryip"][0]["ipaddress"] == elastic_ip.address

        instance.detach_elastic_ip(elastic_ip)

        res = exo.compute.cs.listNics(virtualmachineid=instance.id, fetch_list=True)
        for nic in res:
            if not nic["isdefault"]:
                continue
            assert "secondaryip" not in nic

    def test_attach_private_network(self, exo, privnet, instance):
        private_network = PrivateNetwork.from_cs(exo.compute, privnet())
        instance = Instance.from_cs(exo.compute, instance())

        instance.attach_private_network(private_network=private_network)

        [res] = exo.compute.cs.listNics(
            virtualmachineid=instance.id, networkid=private_network.id, fetch_list=True
        )
        assert res["networkid"] == private_network.id
        assert res["virtualmachineid"] == instance.id

        exo.compute.cs.removeNicFromVirtualMachine(
            virtualmachineid=instance.id, nicid=res["id"]
        )

    def test_detach_private_network(self, exo, privnet, instance):
        private_network = PrivateNetwork.from_cs(exo.compute, privnet())
        instance = Instance.from_cs(exo.compute, instance())

        res = exo.compute.cs.addNicToVirtualMachine(
            virtualmachineid=instance.id, networkid=private_network.id
        )

        [res] = exo.compute.cs.listNics(
            virtualmachineid=instance.id, networkid=private_network.id, fetch_list=True
        )
        assert res["networkid"] == private_network.id
        assert res["virtualmachineid"] == instance.id

        instance.detach_private_network(private_network=private_network)

        res = exo.compute.cs.listNics(
            virtualmachineid=instance.id, networkid=private_network.id, fetch_list=True
        )
        assert len(res) == 0

    def test_set_reverse_dns(self, exo, instance, test_reverse_dns):
        instance = Instance.from_cs(exo.compute, instance())

        instance.set_reverse_dns(record=test_reverse_dns)

        res = exo.compute.cs.queryReverseDnsForVirtualMachine(id=instance.id)
        assert (
            res["virtualmachine"]["nic"][0]["reversedns"][0]["domainname"]
            == test_reverse_dns
        )

    def test_unset_reverse_dns(self, exo, instance, test_reverse_dns):
        instance = Instance.from_cs(exo.compute, instance())

        res = exo.compute.cs.updateReverseDnsForVirtualMachine(
            id=instance.id, domainname=test_reverse_dns
        )
        assert (
            res["virtualmachine"]["nic"][0]["reversedns"][0]["domainname"]
            == test_reverse_dns
        )

        instance.unset_reverse_dns()

        res = exo.compute.cs.queryReverseDnsForVirtualMachine(id=instance.id)
        assert len(res["virtualmachine"]["nic"][0]["reversedns"]) == 0

    def test_delete(self, exo, instance):
        instance = Instance.from_cs(exo.compute, instance(teardown=False))
        instance_name = instance.name

        instance.delete()
        assert instance.id is None

        res = exo.compute.cs.listVirtualMachines(name=instance_name, fetch_list=True)
        assert len(res) == 0

    def test_properties(self, exo, aag, sg, privnet, eip, instance, test_reverse_dns):
        anti_affinity_group = AntiAffinityGroup.from_cs(exo.compute, aag())
        security_group = SecurityGroup.from_cs(exo.compute, sg())
        private_network = PrivateNetwork.from_cs(exo.compute, privnet())
        elastic_ip = ElasticIP.from_cs(exo.compute, eip())
        instance = Instance.from_cs(
            exo.compute,
            instance(
                anti_affinity_groups=[anti_affinity_group.id],
                security_groups=[security_group.id],
                private_networks=[private_network.id],
                teardown=False,
            ),
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

        res = exo.compute.cs.listNics(virtualmachineid=instance.id, fetch_list=True)
        exo.compute.cs.addIpToNic(
            nicid=instance._default_nic(res)["id"], ipaddress=elastic_ip.address
        )
        instance_elastic_ips = list(instance.elastic_ips)
        assert len(instance_elastic_ips) == 1
        assert instance_elastic_ips[0].id == elastic_ip.id

        exo.compute.cs.updateReverseDnsForVirtualMachine(
            id=instance.id, domainname=test_reverse_dns
        )
        assert instance.reverse_dns == test_reverse_dns

        # For some reason the CS deployVirtualMachine response `rootdeviceid`
        # attribute value is "0", so we can't compare it to instance_volume.id
        instance_volume = instance.volume
        assert instance_volume.id is not None
        assert instance_volume.size > 0

        # We have to delete the fixture instance here because of a race condition with
        # the sg fixture teardown than will fail because it can't delete itself while
        # still used by an instance ¯\_(ツ)_/¯
        exo.compute.cs.destroyVirtualMachine(id=instance.id)
