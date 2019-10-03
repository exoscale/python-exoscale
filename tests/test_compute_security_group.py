#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.compute import *


class TestComputeSecurityGroup:
    def test_add_rule(self, exo, sg, test_description):
        security_group = SecurityGroup._from_cs(exo.compute, sg())
        test_network_cidr = "1.1.1.1/32"
        test_port_ingress = "80-81"
        test_protocol_ingress = "tcp"
        test_port_egress = "53"
        test_protocol_egress = "udp"

        security_group_default = SecurityGroup._from_cs(
            exo.compute,
            exo.compute.cs.listSecurityGroups(
                securitygroupname="default", fetch_list=True
            )[0],
        )

        for rule in [
            SecurityGroupRule.ingress(
                description=test_description,
                security_group=security_group_default,
                port=test_port_ingress,
                protocol=test_protocol_ingress,
            ),
            SecurityGroupRule.egress(
                description=test_description,
                network_cidr=test_network_cidr,
                port=test_port_egress,
                protocol=test_protocol_egress,
            ),
        ]:
            security_group.add_rule(rule)

        res = exo.compute.cs.listSecurityGroups(id=security_group.id, fetch_list=True)
        assert len(res[0]["ingressrule"]) == 1
        assert res[0]["ingressrule"][0]["description"] == test_description
        assert res[0]["ingressrule"][0]["securitygroupname"] == "default"
        assert res[0]["ingressrule"][0]["protocol"] == test_protocol_ingress
        assert res[0]["ingressrule"][0]["startport"] == int(
            test_port_ingress.split("-")[0]
        )
        assert res[0]["ingressrule"][0]["endport"] == int(
            test_port_ingress.split("-")[1]
        )
        assert len(res[0]["egressrule"]) == 1
        assert res[0]["egressrule"][0]["description"] == test_description
        assert res[0]["egressrule"][0]["cidr"] == test_network_cidr
        assert res[0]["egressrule"][0]["protocol"] == test_protocol_egress
        assert str(res[0]["egressrule"][0]["startport"]) == test_port_egress
        assert str(res[0]["egressrule"][0]["endport"]) == test_port_egress

    def test_delete(self, exo, sg):
        security_group = SecurityGroup._from_cs(exo.compute, sg(teardown=False))
        security_group_name = security_group.name

        security_group.delete()
        assert security_group.id is None

        res = exo.compute.cs.listSecurityGroups(
            securitygroupname=security_group_name, fetch_list=True
        )
        assert len(res) == 0

    def test_properties(self, exo, sg):
        security_group = SecurityGroup._from_cs(exo.compute, sg())
        security_group_default = SecurityGroup._from_cs(
            exo.compute,
            exo.compute.cs.listSecurityGroups(
                securitygroupname="default", fetch_list=True
            )[0],
        )

        exo.compute.cs.authorizeSecurityGroupIngress(
            securitygroupid=security_group.id,
            usersecuritygrouplist={"group": "default"},
            protocol="tcp",
            startport=8000,
            endport=9000,
        )
        exo.compute.cs.authorizeSecurityGroupEgress(
            securitygroupid=security_group.id,
            protocol="udp",
            cidrlist="0.0.0.0/0",
            startport=53,
            endport=53,
        )

        security_group_ingress_rules = list(security_group.ingress_rules)
        assert len(security_group_ingress_rules) == 1
        assert security_group_ingress_rules[0].type == "ingress"
        assert (
            security_group_ingress_rules[0].security_group.id
            == security_group_default.id
        )
        assert security_group_ingress_rules[0].port == "8000-9000"
        assert security_group_ingress_rules[0].protocol == "tcp"

        security_group_egress_rules = list(security_group.egress_rules)
        assert len(security_group_egress_rules) == 1
        assert security_group_egress_rules[0].type == "egress"
        assert security_group_egress_rules[0].network_cidr == "0.0.0.0/0"
        assert security_group_egress_rules[0].port == "53"
        assert security_group_egress_rules[0].protocol == "udp"
