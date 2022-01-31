#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .conftest import _random_str
from exoscale.api.dns import Domain
from urllib.parse import parse_qs, urlparse


class TestDNSDomain:
    def test_add_record(self, exo, domain, domain_record):
        domain = Domain._from_cs(exo.dns, domain())
        expected = domain_record(
            domain_id=domain.res["id"],
            name=_random_str(),
            record_type="MX",
            content=_random_str(),
            priority=10,
            ttl="1234",
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["name"][0] == domain.res["name"]
            assert params["record_name"][0] == expected["name"]
            assert params["record_type"][0] == expected["record_type"]
            assert params["content"][0] == expected["content"]
            assert params["priority"][0] == str(expected["priority"])
            assert params["ttl"][0] == str(expected["ttl"])

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {"creatednsdomainrecordresponse": expected}

        exo.mock_get("?command=createDnsDomainRecord", _assert_request)

        actual = domain.add_record(
            name=expected["name"],
            type=expected["record_type"],
            content=expected["content"],
            priority=expected["priority"],
            ttl=expected["ttl"],
        )
        assert actual.id == expected["id"]
        assert actual.name == expected["name"]
        assert actual.type == expected["record_type"]
        assert actual.content == expected["content"]
        assert actual.priority == expected["priority"]
        assert actual.ttl == expected["ttl"]

    def test_delete(self, exo, domain):
        domain = Domain._from_cs(exo.dns, domain())

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == str(domain.res["id"])

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {"deletednsdomainresponse": {"success": True}}

        exo.mock_get("?command=deleteDnsDomain", _assert_request)

        domain.delete()
        assert domain.id is None

    def test_properties(self, exo, domain, domain_record):
        domain = Domain._from_cs(exo.dns, domain())
        domain_record = domain_record()

        exo.mock_list("listDnsDomainRecords", [domain_record])

        domain_records = list(domain.records)
        assert len(domain_records) == 1
        assert domain_records[0].id == domain_record["id"]
