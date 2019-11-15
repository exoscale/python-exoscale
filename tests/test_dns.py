#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.dns import *
from .conftest import _random_str


class TestDNS:
    ### Domain

    def test_create_domain(self, exo, test_prefix):
        domain_name = "-".join([test_prefix, _random_str()]) + ".net"

        domain = exo.dns.create_domain(name=domain_name)
        assert domain.id > 0
        assert domain.name == domain_name

        exo.dns.cs.deleteDnsDomain(id=domain.id)

    def test_list_domains(self, exo, domain):
        domain = Domain._from_cs(exo.dns, domain())

        domains = list(exo.dns.list_domains())
        # We cannot guarantee that there will be only our resources in the
        # testing environment, so we ensure we get at least our fixture domain
        assert len(domains) >= 1

    def test_get_domain(self, exo, domain):
        domain1 = Domain._from_cs(exo.dns, domain())

        domain = exo.dns.get_domain(id=domain1.id)
        assert domain.id == domain1.id

        domain = exo.dns.get_domain(name=domain1.name)
        assert domain.id == domain1.id

        with pytest.raises(ResourceNotFoundError) as excinfo:
            domain = exo.dns.get_domain(id=42)
            assert domain is None
        assert excinfo.type == ResourceNotFoundError

        with pytest.raises(ResourceNotFoundError) as excinfo:
            domain = exo.dns.get_domain(name="lolnope.com")
            assert domain is None
        assert excinfo.type == ResourceNotFoundError
