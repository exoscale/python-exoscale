#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from cs import CloudStackApiException
from exoscale.api.dns import *


class TestDNSDomain:
    def test_add_record(self, exo, domain):
        domain = Domain.from_cs(exo.dns, domain())
        domain_record_name = "test-python-exoscale"
        domain_record_type = "MX"
        domain_record_content = "mx1.example.net"
        domain_record_priority = 10
        domain_record_ttl = 1042

        domain.add_record(
            name=domain_record_name,
            type=domain_record_type,
            content=domain_record_content,
            priority=domain_record_priority,
            ttl=domain_record_ttl,
        )

        res = exo.dns.cs.listDnsDomainRecords(id=domain.id, fetch_list=True)
        for record in res:
            if record["name"] == "":
                continue
            assert record["name"] == domain_record_name
            assert record["record_type"] == domain_record_type
            assert record["content"] == domain_record_content
            assert record["priority"] == domain_record_priority
            assert record["ttl"] == domain_record_ttl

    def test_delete(self, exo, domain):
        domain = Domain.from_cs(exo.dns, domain(teardown=False))
        domain_id = domain.id

        domain.delete()
        assert domain.id == None

        res = exo.dns.cs.listDnsDomains(fetch_list=True)
        for i in res:
            assert i["id"] != domain_id

    def test_properties(self, exo, domain):
        domain = Domain.from_cs(exo.dns, domain())
        domain_record_name = "test-python-exoscale"
        domain_record_type = "A"
        domain_record_content = "1.2.3.4"
        domain_record_ttl = 1042

        exo.dns.cs.createDnsDomainRecord(
            name=domain.name,
            record_name=domain_record_name,
            record_type=domain_record_type,
            content=domain_record_content,
            ttl=domain_record_ttl,
        )

        domain_records = list(domain.records)
        assert len(domain_records) > 1
        domain_record = list(r for r in domain_records if r.name == domain_record_name)[
            0
        ]
        assert domain_record.id > 0
        assert domain_record.type == domain_record_type
        assert domain_record.content == domain_record_content
        assert domain_record.ttl == domain_record_ttl
