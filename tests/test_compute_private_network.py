#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.compute import *


class TestComputePrivateNetwork:
    def test_attach_instance(self, exo, privnet, instance):
        private_network = PrivateNetwork.from_cs(exo.compute, privnet())
        instance = Instance.from_cs(exo.compute, instance())

        private_network.attach_instance(instance)

        res = exo.compute.cs.listNics(
            virtualmachineid=instance.id, networkid=private_network.id, fetch_list=True
        )
        assert len(res) == 1
        assert res[0]["networkid"] == private_network.id
        assert res[0]["virtualmachineid"] == instance.id

        for nic in res:
            if nic["isdefault"]:
                continue
            exo.compute.cs.removeNicFromVirtualMachine(
                virtualmachineid=instance.id, nicid=nic["id"]
            )

    def test_detach_instance(self, exo, privnet, instance):
        private_network = PrivateNetwork.from_cs(exo.compute, privnet())
        instance = Instance.from_cs(exo.compute, instance())

        exo.compute.cs.addNicToVirtualMachine(
            virtualmachineid=instance.id, networkid=private_network.id
        )

        [res] = exo.compute.cs.listNics(
            virtualmachineid=instance.id, networkid=private_network.id, fetch_list=True
        )
        assert res["networkid"] == private_network.id
        assert res["virtualmachineid"] == instance.id

        private_network.detach_instance(instance)

        res = exo.compute.cs.listNics(
            virtualmachineid=instance.id, networkid=private_network.id, fetch_list=True
        )
        assert len(res) == 0

    def test_update(self, exo, privnet):
        private_network = PrivateNetwork.from_cs(exo.compute, privnet())
        description_edited = private_network.description + " (edited)"

        private_network.update(description=description_edited)
        assert private_network.description == description_edited

        res = exo.compute.cs.listNetworks(id=private_network.id, fetch_list=True)
        assert res[0]["displaytext"] == description_edited

    def test_delete(self, exo, privnet):
        private_network = PrivateNetwork.from_cs(exo.compute, privnet(teardown=False))
        private_network_id = private_network.id

        private_network.delete()
        assert private_network.id is None

        with pytest.raises(CloudStackApiException) as excinfo:
            res = exo.compute.cs.listNetworks(id=private_network_id, fetch_list=True)
            assert len(res) == 0
        assert excinfo.type == CloudStackApiException
        assert excinfo.value.error["errortext"].find("entity does not exist")

    def test_properties(self, exo, privnet, instance):
        private_network = PrivateNetwork.from_cs(exo.compute, privnet())
        instance = Instance.from_cs(exo.compute, instance())

        res = exo.compute.cs.addNicToVirtualMachine(
            virtualmachineid=instance.id, networkid=private_network.id
        )

        private_network_instances = list(private_network.instances)
        assert len(private_network_instances) == 1
        assert private_network_instances[0].name == instance.name

        for nic in res["virtualmachine"]["nic"]:
            if nic["isdefault"]:
                continue
            exo.compute.cs.removeNicFromVirtualMachine(
                virtualmachineid=instance.id, nicid=nic["id"]
            )
