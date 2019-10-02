#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from cs import CloudStackApiException
from exoscale.api.dns import *


class TestDNSDomainRecord:
    def test_update(self, exo, domain):
        domain = Domain._from_cs(exo.dns, domain())
        domain_record_name = "test-python-exoscale"
        domain_record_name_edited = "test-python-exoscale-edited"
        domain_record_type = "MX"
        domain_record_content = "mx1.example.net"
        domain_record_content_edited = "mx2.example.net"
        domain_record_priority = 10
        domain_record_priority_edited = 20
        domain_record_ttl = 1042
        domain_record_ttl_edited = 1043

        exo.dns.cs.createDnsDomainRecord(
            name=domain.name,
            record_name=domain_record_name,
            record_type=domain_record_type,
            content=domain_record_content,
            ttl=domain_record_ttl,
            prio=domain_record_priority,
        )

        res = exo.dns.cs.listDnsDomainRecords(id=domain.id, fetch_list=True)
        for r in res:
            if r["name"] == "":
                continue

            domain_record = DomainRecord._from_cs(exo.dns, r, domain)

            domain_record.update(
                name=domain_record_name_edited,
                content=domain_record_content_edited,
                priority=domain_record_priority_edited,
                ttl=domain_record_ttl_edited,
            )

        res = exo.dns.cs.listDnsDomainRecords(id=domain.id, fetch_list=True)
        for r in res:
            if r["name"] == "":
                continue
            assert r["name"] == domain_record_name_edited
            assert r["content"] == domain_record_content_edited
            assert r["priority"] == domain_record_priority_edited
            assert r["ttl"] == domain_record_ttl_edited

    def test_delete(self, exo, domain):
        domain = Domain._from_cs(exo.dns, domain())
        domain_record_name = "test-python-exoscale"
        domain_record_type = "MX"
        domain_record_content = "mx1.example.net"
        domain_record_priority = 10
        domain_record_ttl = 1042

        exo.dns.cs.createDnsDomainRecord(
            name=domain.name,
            record_name=domain_record_name,
            record_type=domain_record_type,
            content=domain_record_content,
            ttl=domain_record_ttl,
            prio=domain_record_priority,
        )

        res = exo.dns.cs.listDnsDomainRecords(id=domain.id, fetch_list=True)
        for r in res:
            if r["name"] == "":
                continue

            domain_record = DomainRecord._from_cs(exo.dns, r, domain)

            domain_record.delete()

        res = exo.dns.cs.listDnsDomainRecords(id=domain.id, fetch_list=True)
        assert len(list(r for r in res if r["name"] != "")) == 0
