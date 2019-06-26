#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.compute import *


class TestComputeInstanceVolume:
    def test_resize(self, exo, instance):
        instance = Instance.from_cs(exo.compute, instance(start=False))

        res = exo.compute.cs.listVolumes(virtualmachineid=instance.id, fetch_list=True)
        assert res[0]["size"] == 10737418240  # 10 GB

        volume = InstanceVolume.from_cs(exo.compute, res[0])
        volume.resize(size=20)

        res = exo.compute.cs.listVolumes(virtualmachineid=instance.id, fetch_list=True)
        assert res[0]["size"] == 21474836480  # 20 GB

    def test_snapshot(self, exo, instance):
        instance = Instance.from_cs(exo.compute, instance())

        res = exo.compute.cs.listVolumes(virtualmachineid=instance.id, fetch_list=True)
        instance_volume = InstanceVolume.from_cs(exo.compute, res[0])

        snapshot = instance_volume.snapshot()
        assert snapshot.id != ""
        assert snapshot.date != ""
        assert snapshot.size > 0

    def test_properties(self, exo, instance):
        instance = Instance.from_cs(exo.compute, instance())

        res = exo.compute.cs.listVolumes(virtualmachineid=instance.id, fetch_list=True)
        instance_volume = InstanceVolume.from_cs(exo.compute, res[0])

        res = exo.compute.cs.createSnapshot(volumeid=instance_volume.id)

        instance_volume_snapshots = list(instance_volume.snapshots)
        assert len(instance_volume_snapshots) == 1
        assert instance_volume_snapshots[0].id == res["snapshot"]["id"]
