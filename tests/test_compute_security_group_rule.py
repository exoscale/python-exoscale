#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.compute import *


class TestComputeSecurityGroupRule:
    def test_delete(self, exo, sg):
        security_group = SecurityGroup.from_cs(exo.compute, sg())

        rule1 = exo.compute.cs.authorizeSecurityGroupIngress(
            securitygroupid=security_group.id,
            cidrlist="0.0.0.0/0",
            protocol="TCP",
            startport=80,
            endport=80,
        )["securitygroup"]["ingressrule"][0]
        rule2 = exo.compute.cs.authorizeSecurityGroupEgress(
            securitygroupid=security_group.id,
            protocol="TCP",
            cidrlist="0.0.0.0/0",
            startport=80,
            endport=80,
        )["securitygroup"]["egressrule"][0]

        res = exo.compute.cs.listSecurityGroups(id=security_group.id, fetch_list=True)
        SecurityGroupRule.from_cs(
            compute=exo.compute, type="ingress", res=res[0]["ingressrule"][0]
        ).delete()
        SecurityGroupRule.from_cs(
            compute=exo.compute, type="egress", res=res[0]["egressrule"][0]
        ).delete()

        res = exo.compute.cs.listSecurityGroups(id=security_group.id, fetch_list=True)
        assert len(res[0]["ingressrule"]) == 0
        assert len(res[0]["egressrule"]) == 0

    def test_parse_port(self):
        rule = SecurityGroupRule(type="ingress")
        assert rule._parse_port() == (None, None)

        rule = SecurityGroupRule(type="ingress", port="80")
        assert rule._parse_port() == (80, 80)

        rule = SecurityGroupRule(type="ingress", port="80-81")
        assert rule._parse_port() == (80, 81)
