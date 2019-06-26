#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.runstatus import *
from datetime import timezone


class TestRunstatusPageMaintenance:
    def test_update(self, exo, runstatus_page):
        page = Page.from_rs(exo.runstatus, runstatus_page())
        test_maintenance_title = "Database server upgrade"
        test_maintenance_description = (
            "We're upgrading the database server hardware to add more memory"
        )
        test_maintenance_service = "db"
        test_maintenance_start_date = datetime(2019, 8, 2, 4, 0, tzinfo=timezone.utc)
        test_maintenance_end_date = datetime(2019, 8, 2, 5, 0, tzinfo=timezone.utc)

        exo.runstatus._post(
            url="/pages/{p}/services".format(p=page.name),
            json={"name": test_maintenance_service},
        )

        exo.runstatus._post(
            url="/pages/{p}/maintenances".format(p=page.name),
            json={
                "title": test_maintenance_title,
                "description": test_maintenance_description,
                "start_date": test_maintenance_start_date.isoformat(),
                "end_date": test_maintenance_end_date.isoformat(),
                "services": [test_maintenance_service],
            },
        )

        res = exo.runstatus._get(
            url="/pages/{p}/maintenances".format(p=page.name)
        ).json()
        maintenance = Maintenance.from_rs(exo.runstatus, res["results"][0], page)

        maintenance.update(description="Stopping server", status="in-progress")
        maintenance.update(description="Upgrading memory")
        maintenance.update(description="Restarting server")

        res = exo.runstatus._get(
            url="/pages/{p}/maintenances/{i}/events".format(
                p=page.name, i=maintenance.id
            )
        ).json()
        assert len(res["results"]) == 3
        assert res["results"][0]["text"] == "Restarting server"
        assert res["results"][0]["status"] == "in-progress"
        assert res["results"][1]["text"] == "Upgrading memory"
        assert res["results"][1]["status"] == "in-progress"
        assert res["results"][2]["text"] == "Stopping server"
        assert res["results"][2]["status"] == "in-progress"

    def test_close(self, exo, runstatus_page):
        page = Page.from_rs(exo.runstatus, runstatus_page())
        test_maintenance_title = "Database server upgrade"
        test_maintenance_description = (
            "We're upgrading the database server hardware to add more memory"
        )
        test_maintenance_service = "db"
        test_maintenance_start_date = datetime(2019, 8, 2, 4, 0, tzinfo=timezone.utc)
        test_maintenance_end_date = datetime(2019, 8, 2, 5, 0, tzinfo=timezone.utc)

        exo.runstatus._post(
            url="/pages/{p}/services".format(p=page.name),
            json={"name": test_maintenance_service},
        )

        exo.runstatus._post(
            url="/pages/{p}/maintenances".format(p=page.name),
            json={
                "title": test_maintenance_title,
                "description": test_maintenance_description,
                "start_date": test_maintenance_start_date.isoformat(),
                "end_date": test_maintenance_end_date.isoformat(),
                "services": [test_maintenance_service],
            },
        )

        res = exo.runstatus._get(
            url="/pages/{p}/maintenances".format(p=page.name)
        ).json()
        maintenance = Maintenance.from_rs(exo.runstatus, res["results"][0], page)

        maintenance.close("We're done here")

        res = exo.runstatus._get(
            url="/pages/{p}/maintenances/{i}/events".format(
                p=page.name, i=maintenance.id
            )
        ).json()
        assert len(res["results"]) == 1
        assert res["results"][0]["text"] == "We're done here"
        assert res["results"][0]["status"] == "completed"

    def test_properties(self, exo, runstatus_page):
        page = Page.from_rs(exo.runstatus, runstatus_page())
        test_maintenance_title = "Database server upgrade"
        test_maintenance_title_edited = "Database server upgrade (edited)"
        test_maintenance_description = (
            "We're upgrading the database server hardware to add more memory"
        )
        test_maintenance_description_edited = (
            "We're upgrading the database server hardware to add more memory (edited)"
        )
        test_maintenance_services = ["db1", "db2"]
        test_maintenance_start_date = datetime(2019, 8, 2, 4, 0, tzinfo=timezone.utc)
        test_maintenance_start_date_edited = datetime(
            2019, 8, 2, 14, 0, tzinfo=timezone.utc
        )
        test_maintenance_end_date = datetime(2019, 8, 2, 5, 0, tzinfo=timezone.utc)
        test_maintenance_end_date = datetime(2019, 8, 2, 15, 0, tzinfo=timezone.utc)

        for i in test_maintenance_services:
            exo.runstatus._post(
                url="/pages/{p}/services".format(p=page.name), json={"name": i}
            )

        exo.runstatus._post(
            url="/pages/{p}/maintenances".format(p=page.name),
            json={
                "title": test_maintenance_title,
                "description": test_maintenance_description,
                "start_date": test_maintenance_start_date.isoformat(),
                "end_date": test_maintenance_end_date.isoformat(),
                "services": [test_maintenance_services[0]],
            },
        )

        res = exo.runstatus._get(
            url="/pages/{p}/maintenances".format(p=page.name)
        ).json()
        maintenance = Maintenance.from_rs(exo.runstatus, res["results"][0], page)

        maintenance.title = test_maintenance_title_edited
        assert maintenance.title == test_maintenance_title_edited

        maintenance.description = test_maintenance_description_edited
        assert maintenance.description == test_maintenance_description_edited

        maintenance.services = [test_maintenance_services[1]]
        assert maintenance.services == [test_maintenance_services[1]]

        for i in [1, 2, 3]:
            exo.runstatus._post(
                url="/pages/{p}/maintenances/{i}/events".format(
                    p=page.name, i=maintenance.id
                ),
                json={"text": "Update #{}".format(i), "status": maintenance.status},
            )

        maintenance_events = list(maintenance.events)
        assert len(maintenance_events) == 3
        assert maintenance_events[0].description == "Update #3"
        assert maintenance_events[1].description == "Update #2"
        assert maintenance_events[2].description == "Update #1"
