#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .conftest import _random_str, _random_uuid
from exoscale.api.compute import SecurityGroup, SecurityGroupRule
from urllib.parse import parse_qs, urlparse


class TestComputeSecurityGroup:
    def test_add_rule(self, exo, sg):
        rule_description = _random_str()
        rule_network_cidr = "1.1.1.1/32"
        rule_start_port_ingress = "80"
        rule_end_port_ingress = "81"
        rule_protocol_ingress = "tcp"
        rule_port_egress = "53"
        rule_protocol_egress = "udp"
        security_group_default = SecurityGroup._from_cs(
            exo.compute, sg(name="default")
        )
        security_group = SecurityGroup._from_cs(exo.compute, sg())

        def _assert_request_ingress(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["securitygroupid"][0] == security_group.res["id"]
            assert params["description"][0] == rule_description
            assert (
                params["usersecuritygrouplist[0].group"][0]
                == security_group_default.res["name"]
            )
            assert params["startport"][0] == rule_start_port_ingress
            assert params["endport"][0] == rule_end_port_ingress
            assert params["protocol"][0] == rule_protocol_ingress

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "authorizesecuritygroupingressresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get(
            "?command=authorizeSecurityGroupIngress", _assert_request_ingress
        )
        exo.mock_query_async_job_result({"success": True})

        security_group.add_rule(
            SecurityGroupRule.ingress(
                description=rule_description,
                security_group=security_group_default,
                port="{}-{}".format(
                    rule_start_port_ingress, rule_end_port_ingress
                ),
                protocol=rule_protocol_ingress,
            )
        )

        def _assert_request_egress(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["securitygroupid"][0] == security_group.res["id"]
            assert params["description"][0] == rule_description
            assert params["cidrlist"][0] == rule_network_cidr
            assert params["startport"][0] == rule_port_egress
            assert params["endport"][0] == rule_port_egress
            assert params["protocol"][0] == rule_protocol_egress

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "authorizesecuritygroupegressresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get(
            "?command=authorizeSecurityGroupEgress", _assert_request_egress
        )
        exo.mock_query_async_job_result({"success": True})

        security_group.add_rule(
            SecurityGroupRule.egress(
                description=rule_description,
                network_cidr=rule_network_cidr,
                port=rule_port_egress,
                protocol=rule_protocol_egress,
            )
        )

    def test_delete(self, exo, sg):
        security_group = SecurityGroup._from_cs(exo.compute, sg())

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == security_group.res["id"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "deleteffinitygroupresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=deleteSecurityGroup", _assert_request)
        exo.mock_query_async_job_result({"success": True})

        security_group.delete()
        assert security_group.id is None

    def test_properties(self, exo, sg):
        SecurityGroup._from_cs(exo.compute, sg(name="default"))
        security_group = SecurityGroup._from_cs(
            exo.compute,
            sg(
                ingress=[
                    {
                        "ruleid": _random_uuid(),
                        "securitygroupname": "default",
                        "protocol": "tcp",
                        "startport": 8000,
                        "endport": 9000,
                    }
                ],
                egress=[
                    {
                        "ruleid": _random_uuid(),
                        "protocol": "udp",
                        "cidr": "0.0.0.0/0",
                        "startport": 53,
                        "endport": 53,
                    }
                ],
            ),
        )

        exo.mock_list("listSecurityGroups", [security_group.res])

        security_group_ingress_rules = list(security_group.ingress_rules)
        assert len(security_group_ingress_rules) == 1
        assert security_group_ingress_rules[0].type == "ingress"

        security_group_egress_rules = list(security_group.egress_rules)
        assert len(security_group_egress_rules) == 1
        assert security_group_egress_rules[0].type == "egress"
