#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.runstatus import *


class TestRunstatusPageService:
    def test_delete(self, exo, runstatus_page):
        page = Page.from_rs(exo.runstatus, runstatus_page(teardown=False))
        service_name = "a"

        exo.runstatus._post(
            url="/pages/{p}/services".format(p=page.name), json={"name": service_name}
        )

        res = exo.runstatus._get(url="/pages/{p}/services".format(p=page.name)).json()
        service = Service.from_rs(exo.runstatus, res["results"][0], page=page)

        service.delete()
        assert service.id == None

        res = exo.runstatus._get(url="/pages/{p}/services".format(p=page.name)).json()
        assert len(res["results"]) == 0

    def test_properties(self, exo, runstatus_page):
        page = Page.from_rs(exo.runstatus, runstatus_page(teardown=False))
        service_name = "a"

        exo.runstatus._post(
            url="/pages/{p}/services".format(p=page.name), json={"name": service_name}
        )

        res = exo.runstatus._get(url="/pages/{p}/services".format(p=page.name)).json()
        service = Service.from_rs(exo.runstatus, res["results"][0], page=page)

        assert service.state == "operational"
