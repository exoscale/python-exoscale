#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api import ResourceNotFoundError
from exoscale.api.compute import *
from cs import CloudStackApiException
from datetime import datetime, timedelta
from time import sleep


class TestComputeInstancePool:
    def test_update(self, exo, zone, instance_pool):
        zone = Zone._from_cs(zone("ch-gva-2"))
        instance_pool = InstancePool._from_cs(
            exo.compute, instance_pool(zone_id=zone.id)
        )
        name_edited = instance_pool.name + "-edited"
        description_edited = instance_pool.description + " (edited)"

        instance_pool.update(name=name_edited, description=description_edited)

        [actual_instance_pool] = exo.compute.cs.getInstancePool(
            id=instance_pool.id, zoneid=instance_pool.zone.id, fetch_list=True
        )
        assert instance_pool.name == name_edited
        assert actual_instance_pool["name"] == name_edited
        assert instance_pool.description == description_edited
        assert actual_instance_pool["description"] == description_edited

    def test_scale(self, exo, zone, instance_pool):
        zone = Zone._from_cs(zone("ch-gva-2"))
        instance_pool = InstancePool._from_cs(
            exo.compute, instance_pool(zone_id=zone.id)
        )

        instance_pool.scale(2)

        [actual_instance_pool] = exo.compute.cs.getInstancePool(
            id=instance_pool.id, zoneid=instance_pool.zone.id, fetch_list=True
        )
        assert instance_pool.size == 2
        assert actual_instance_pool["size"] == 2

    def test_delete_no_wait(self, exo, zone, instance_pool):
        zone = Zone._from_cs(zone("ch-gva-2"))
        instance_pool = InstancePool._from_cs(
            exo.compute, instance_pool(zone_id=zone.id, teardown=False)
        )
        instance_pool_id = instance_pool.id
        instance_pool_zone_id = instance_pool.zone.id

        # Let's wait until the Instance Pool fixture state stabilizes before destroying
        # it, otherwise we'll likely run into a race condition
        t = datetime.now()
        while exo.compute.cs.getInstancePool(
            zoneid=zone.id, id=instance_pool.id, fetch_list=True
        )[0]["state"] == "scaling-up" and datetime.now() - t < timedelta(minutes=5):
            sleep(10)

        instance_pool.delete(wait=False)
        assert instance_pool.id is None

        # Wait a few seconds for the deletion process to kick in
        sleep(5)

        [actual_instance_pool] = exo.compute.cs.getInstancePool(
            id=instance_pool_id, zoneid=instance_pool_zone_id, fetch_list=True
        )
        assert actual_instance_pool["state"] == "destroying"

    def test_delete_wait(self, exo, zone, instance_pool):
        zone = Zone._from_cs(zone("ch-gva-2"))
        instance_pool = InstancePool._from_cs(
            exo.compute, instance_pool(zone_id=zone.id, teardown=False)
        )
        instance_pool_id = instance_pool.id
        instance_pool_zone_id = instance_pool.zone.id

        # Let's wait until the Instance Pool fixture state stabilizes before destroying
        # it, otherwise we'll likely run into a race condition
        t = datetime.now()
        while exo.compute.cs.getInstancePool(
            zoneid=zone.id, id=instance_pool.id, fetch_list=True
        )[0]["state"] == "scaling-up" and datetime.now() - t < timedelta(minutes=5):
            sleep(10)

        instance_pool.delete()
        assert instance_pool.id is None

        with pytest.raises(CloudStackApiException) as excinfo:
            exo.compute.cs.getInstancePool(
                id=instance_pool_id, zoneid=instance_pool_zone_id, fetch_list=True
            )

    def test_properties(self, exo, zone, aag, sg, privnet, instance_pool):
        zone = Zone._from_cs(zone())
        anti_affinity_group = AntiAffinityGroup._from_cs(exo.compute, aag())
        security_group = SecurityGroup._from_cs(exo.compute, sg())
        private_network = PrivateNetwork._from_cs(exo.compute, privnet())
        instance_pool = InstancePool._from_cs(
            exo.compute,
            instance_pool(
                zone_id=zone.id,
                size=1,
                anti_affinity_groups=[anti_affinity_group.id],
                security_groups=[security_group.id],
                private_networks=[private_network.id],
                teardown=False,
            ),
        )

        instance_pool_instances = list(instance_pool.instances)
        assert len(instance_pool_instances) == 1
        assert instance_pool_instances[0].instance_pool.id == instance_pool.id
        assert instance_pool.state in ["scaling-up", "running"]

        instance_pool_anti_affinity_groups = list(instance_pool.anti_affinity_groups)
        assert len(instance_pool_anti_affinity_groups) == 1
        assert instance_pool_anti_affinity_groups[0].id == anti_affinity_group.id

        instance_pool_security_groups = list(instance_pool.security_groups)
        assert len(instance_pool_security_groups) == 1
        assert instance_pool_security_groups[0].id == security_group.id

        instance_pool_private_networks = list(instance_pool.private_networks)
        assert len(instance_pool_private_networks) == 1
        assert instance_pool_private_networks[0].id == private_network.id

        # We have to delete the fixture Instance Pool and ensure its member instance is
        # actually deleted here because of a race condition with the AAG/SG fixtures
        # teardown than will fail because it can't delete itself while still used by an
        # instance ¯\_(ツ)_/¯
        exo.compute.cs.destroyInstancePool(id=instance_pool.id, zoneid=zone.id)
        t = datetime.now()
        try:
            while exo.compute.get_instance(
                zone=zone, id=instance_pool_instances[0].id
            ) != None and datetime.now() - t < timedelta(minutes=5):
                sleep(10)
        except ResourceNotFoundError:
            return
