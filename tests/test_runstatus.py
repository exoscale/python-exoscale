#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.runstatus import *
from .conftest import _random_str


class TestRunstatus:
    ### Page

    def test_create_page(self, exo, test_prefix):
        page_name = "-".join([test_prefix, _random_str()])

        page = exo.runstatus.create_page(name=page_name)
        assert page.id > 0
        assert page.name == page_name

        exo.runstatus._delete(url="/pages/{p}".format(p=page_name))

    def test_list_pages(self, exo, runstatus_page):
        page = Page._from_rs(exo.runstatus, runstatus_page())

        pages = list(exo.runstatus.list_pages())
        # We cannot guarantee that there will be only our resources in the
        # testing environment, so we ensure we get at least our fixture page
        assert len(pages) >= 1

    def test_get_page(self, exo, runstatus_page):
        page1 = Page._from_rs(exo.runstatus, runstatus_page())

        page = exo.runstatus.get_page(name=page1.name)
        assert page.name == page1.name

        with pytest.raises(ResourceNotFoundError) as excinfo:
            page = exo.runstatus.get_page(name="lolnope")
            assert page is None
        assert excinfo.type == ResourceNotFoundError
