#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .conftest import _random_str
from exoscale.api.dns import Domain, DomainRecord
from urllib.parse import parse_qs, urlparse


class TestDNSDomainRecord:
    def test_update(self, exo, domain, domain_record):
        domain = Domain._from_cs(exo.dns, domain())
        domain_record = DomainRecord._from_cs(
            exo.dns, domain_record(domain_id=domain.res["id"]), domain
        )
        domain_record_name = _random_str()
        domain_record_content = _random_str()
        domain_record_priority = 10
        domain_record_ttl = 1234

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["name"][0] == domain.res["name"]
            assert params["record_name"][0] == domain_record_name
            assert params["content"][0] == domain_record_content
            assert params["priority"][0] == str(domain_record_priority)
            assert params["ttl"][0] == str(domain_record_ttl)

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {
                "updatednsdomainrecordresponse": {
                    **domain_record.res,
                    **{
                        "name": domain_record_name,
                        "content": domain_record_content,
                        "priority": domain_record_priority,
                        "ttl": domain_record_ttl,
                    },
                }
            }

        exo.mock_get("?command=updateDnsDomainRecord", _assert_request)
        domain_record.update(
            name=domain_record_name,
            content=domain_record_content,
            priority=domain_record_priority,
            ttl=domain_record_ttl,
        )
        assert domain_record.name == domain_record_name
        assert domain_record.content == domain_record_content
        assert domain_record.priority == domain_record_priority
        assert domain_record.ttl == domain_record_ttl

    def test_delete(self, exo, domain, domain_record):
        domain = Domain._from_cs(exo.dns, domain())
        domain_record = DomainRecord._from_cs(
            exo.dns, domain_record(domain_id=domain.res["id"]), domain
        )

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["id"][0] == str(domain.res["id"])

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {"deletednsdomainrecordresponse": {"success": True}}

        exo.mock_get("?command=deleteDnsDomainRecord", _assert_request)

        domain_record.delete()
        assert domain_record.id is None
