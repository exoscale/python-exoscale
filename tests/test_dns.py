#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.dns import ResourceNotFoundError
from .conftest import _random_str
from urllib.parse import parse_qs, urlparse


class TestDNS:
    # Domain

    def test_create_domain(self, exo, domain):
        domain_name = _random_str() + ".com"
        expected = domain(name=domain_name)

        def _assert_request(request, context):
            params = parse_qs(urlparse(request.url).query)
            assert params["name"][0] == domain_name

            context.status_code = 200
            context.headers["Content-Type"] = "application/json"
            return {"creatednsdomainresponse": {"dnsdomain": expected}}

        exo.mock_get("?command=createDnsDomain", _assert_request)

        actual = exo.dns.create_domain(name=domain_name)
        assert actual.id == expected["id"]
        assert actual.name == expected["name"]
        assert actual.unicode_name == expected["unicodename"]

    def test_list_domains(self, exo, domain):
        expected = domain()

        exo.mock_list("listDnsDomains", [expected])
        actual = list(exo.dns.list_domains())
        assert len(actual) == 1
        assert actual[0].id == expected["id"]

    def test_get_domain(self, exo, domain):
        expected = domain()

        exo.mock_list("listDnsDomains", [expected])

        actual = exo.dns.get_domain(id=expected["id"])
        assert actual.id == expected["id"]

        actual = exo.dns.get_domain(name=expected["name"])
        assert actual.id == expected["id"]

        with pytest.raises(ResourceNotFoundError) as excinfo:
            exo.mock_get(
                "?command=listDnsDomains", {"listdnsdomainsreponse": {}}
            )
            actual = exo.dns.get_domain(name="lolnope")
            assert actual is None
        assert excinfo.type == ResourceNotFoundError
