#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.compute import *


class TestComputeAntiAffinityGroup:
    def test_delete(self, exo, aag):
        anti_affinity_group = AntiAffinityGroup._from_cs(
            exo.compute, aag(teardown=False)
        )
        anti_affinity_group_name = anti_affinity_group.name

        anti_affinity_group.delete()
        assert anti_affinity_group.id is None

        res = exo.compute.cs.listAffinityGroups(
            name=anti_affinity_group_name, fetch_list=True
        )
        assert len(res) == 0

    def test_properties(self, exo, aag, instance):
        anti_affinity_group = AntiAffinityGroup._from_cs(exo.compute, aag())
        instance = Instance._from_cs(
            exo.compute, instance(anti_affinity_groups=[anti_affinity_group.id])
        )

        anti_affinity_group_instances = list(anti_affinity_group.instances)
        assert len(anti_affinity_group_instances) == 1
        assert anti_affinity_group_instances[0].name == instance.name
