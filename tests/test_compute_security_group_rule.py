#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from .conftest import _random_str, _random_uuid
from exoscale.api.compute import *
from urllib.parse import parse_qs, urlparse


class TestComputeSecurityGroupRule:
    def test_delete(self, exo, sg):
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

        def _assert_request_ingress(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == security_group.res["ingressrule"][0]["ruleid"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "revokesecuritygroupingressresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=revokeSecurityGroupIngress", _assert_request_ingress)
        exo.mock_query_async_job_result({"success": True})

        ingress_rule = list(security_group.ingress_rules)[0]
        ingress_rule.delete()
        assert ingress_rule.id is None

        def _assert_request_egress(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == security_group.res["egressrule"][0]["ruleid"]

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "revokesecuritygroupegressresponse": {
                    "id": _random_uuid(),
                    "jobid": _random_uuid(),
                }
            }

        exo.mock_get("?command=revokeSecurityGroupEgress", _assert_request_egress)
        exo.mock_query_async_job_result({"success": True})

        egress_rule = list(security_group.egress_rules)[0]
        egress_rule.delete()
        assert egress_rule.id is None

    def test_parse_port(self):
        rule = SecurityGroupRule(type="ingress")
        assert rule._parse_port() == (None, None)

        rule = SecurityGroupRule(type="ingress", port="80")
        assert rule._parse_port() == (80, 80)

        rule = SecurityGroupRule(type="ingress", port="80-81")
        assert rule._parse_port() == (80, 81)
