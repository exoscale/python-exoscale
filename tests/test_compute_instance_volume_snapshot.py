#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.compute import *


class TestComputeInstanceVolumeSnapshot:
    def test_revert(self, exo, instance):
        instance = Instance._from_cs(exo.compute, instance())

        res = exo.compute.cs.createSnapshot(volumeid=instance.volume_id)
        snapshot = InstanceVolumeSnapshot._from_cs(exo.compute, res["snapshot"])

        res = exo.compute.cs.stopVirtualMachine(id=instance.id)
        assert res["virtualmachine"]["state"].lower() in ["stopping", "stopped"]

        snapshot.revert()
        # We don't have a way to figure out if the snapshot revert has actually worked,
        # so we'll consider that no exception is an OK -- no news is good news!

    def test_delete(self, exo, instance):
        instance = Instance._from_cs(exo.compute, instance())

        res = exo.compute.cs.createSnapshot(volumeid=instance.volume_id)
        snapshot = InstanceVolumeSnapshot._from_cs(exo.compute, res["snapshot"])

        snapshot.delete()
        assert snapshot.id is None

        res = exo.compute.cs.listSnapshots(volumeid=instance.volume_id, fetch_list=True)
        assert len(res) == 0

    def test_properties(self, exo, instance):
        instance = Instance._from_cs(exo.compute, instance())

        res = exo.compute.cs.createSnapshot(volumeid=instance.volume_id)
        instance_volume_snapshot = InstanceVolumeSnapshot._from_cs(
            exo.compute, res["snapshot"]
        )
        assert instance_volume_snapshot.state == "exported"

    def test_export(self, exo, instance):
        instance = Instance._from_cs(exo.compute, instance())

        res = exo.compute.cs.createSnapshot(volumeid=instance.volume_id)
        snapshot = InstanceVolumeSnapshot._from_cs(exo.compute, res["snapshot"])
        assert snapshot.state == "exported"

        res = snapshot.export()
        assert snapshot.state == "exported"
        assert "presignedurl" in res
