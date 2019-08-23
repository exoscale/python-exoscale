#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.runstatus import *
from datetime import timezone


class TestRunstatusPage:
    def test_add_service(self, exo, runstatus_page):
        page = Page.from_rs(exo.runstatus, runstatus_page())

        page.add_service(name="test")

        res = exo.runstatus._get(url="/pages/{p}/services".format(p=page.name)).json()
        assert len(res["results"]) == 1
        assert res["results"][0]["name"] == "test"

    def test_add_incident(self, exo, runstatus_page):
        page = Page.from_rs(exo.runstatus, runstatus_page())
        test_incident_title = "Everything's on fire"
        test_incident_description = "It's fine ¯\\_(ツ)_/¯"
        test_incident_state = "major_outage"
        test_incident_status = "identified"
        test_incident_services = ["a", "b", "c"]

        for i in test_incident_services:
            exo.runstatus._post(
                url="/pages/{p}/services".format(p=page.name), json={"name": i}
            )

        page.add_incident(
            title=test_incident_title,
            description=test_incident_description,
            state=test_incident_state,
            status=test_incident_status,
            services=test_incident_services,
        )

        res = exo.runstatus._get(url="/pages/{p}/incidents".format(p=page.name)).json()
        assert len(res["results"]) == 1
        assert res["results"][0]["title"] == test_incident_title
        assert res["results"][0]["state"] == test_incident_state
        assert res["results"][0]["status"] == test_incident_status
        assert res["results"][0]["services"] == test_incident_services

    def test_add_maintenance(self, exo, runstatus_page):
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

        page.add_maintenance(
            title=test_maintenance_title,
            description=test_maintenance_description,
            start_date=test_maintenance_start_date,
            end_date=test_maintenance_end_date,
            services=[test_maintenance_service],
        )

        res = exo.runstatus._get(
            url="/pages/{p}/maintenances".format(p=page.name)
        ).json()
        assert len(res["results"]) == 1
        assert res["results"][0]["title"] == test_maintenance_title
        assert res["results"][0]["description"] == test_maintenance_description
        assert (
            datetime.strptime(res["results"][0]["start_date"], "%Y-%m-%dT%H:%M:%S%z")
            == test_maintenance_start_date
        )
        assert (
            datetime.strptime(res["results"][0]["end_date"], "%Y-%m-%dT%H:%M:%S%z")
            == test_maintenance_end_date
        )
        assert res["results"][0]["services"] == [test_maintenance_service]

    def test_delete(self, exo, runstatus_page):
        page = Page.from_rs(exo.runstatus, runstatus_page(teardown=False))

        page.delete()
        assert page.id is None

        with pytest.raises(ResourceNotFoundError) as excinfo:
            res = exo.runstatus._get(url="/pages/{p}".format(p=page.name))
        assert excinfo.type == ResourceNotFoundError

    def test_update(self, exo, runstatus_page):
        page = Page.from_rs(exo.runstatus, runstatus_page())
        test_page_title_edited = "python-exoscale"
        test_page_default_status_message_edited = "It's all good in the hood"
        test_page_custom_domain_edited = "status.example.net"
        test_page_time_zone_edited = "Europe/Zurich"

        page.update(
            title=test_page_title_edited,
            default_status_message=test_page_default_status_message_edited,
            custom_domain=test_page_custom_domain_edited,
            time_zone=test_page_time_zone_edited,
        )

        res = exo.runstatus._get(url="/pages/{p}".format(p=page.name)).json()
        assert res["title"] == test_page_title_edited
        assert page.title == test_page_title_edited
        assert res["ok_text"] == test_page_default_status_message_edited
        assert page.default_status_message == test_page_default_status_message_edited
        assert res["domain"] == test_page_custom_domain_edited
        assert page.custom_domain == test_page_custom_domain_edited
        assert res["time_zone"] == test_page_time_zone_edited
        assert page.time_zone == test_page_time_zone_edited

    def test_properties(self, exo, runstatus_page):
        page = Page.from_rs(exo.runstatus, runstatus_page())
        test_page_service_name = "python-exoscale"
        test_incident_title = "Everything's on fire"
        test_incident_description = "It's fine ¯\\_(ツ)_/¯"
        test_incident_state = "major_outage"
        test_incident_status = "identified"
        test_maintenance_title = "Database server upgrade"
        test_maintenance_description = (
            "We're upgrading the database server hardware to add more memory"
        )
        test_maintenance_start_date = datetime(2019, 8, 2, 4, 0, tzinfo=timezone.utc)
        test_maintenance_end_date = datetime(2019, 8, 2, 5, 0, tzinfo=timezone.utc)

        exo.runstatus._post(
            url="/pages/{p}/services".format(p=page.name),
            json={"name": test_page_service_name},
        )
        page_services = list(page.services)
        assert len(page_services)
        assert page_services[0].name == test_page_service_name

        exo.runstatus._post(
            url="/pages/{p}/incidents".format(p=page.name),
            json={
                "title": test_incident_title,
                "status_text": test_incident_description,
                "status": test_incident_status,
                "state": test_incident_state,
                "services": [test_page_service_name],
            },
        )
        incidents = list(page.incidents)
        assert len(incidents) == 1
        assert incidents[0].id > 0
        assert incidents[0].title == test_incident_title
        assert type(incidents[0].start_date) == datetime
        assert incidents[0].state == test_incident_state
        assert incidents[0].status == test_incident_status
        assert incidents[0].services == [test_page_service_name]
        assert incidents[0].page.id == page.id

        exo.runstatus._post(
            url="/pages/{p}/maintenances".format(p=page.name),
            json={
                "title": test_maintenance_title,
                "description": test_maintenance_description,
                "start_date": test_maintenance_start_date.isoformat(),
                "end_date": test_maintenance_end_date.isoformat(),
                "services": [test_page_service_name],
            },
        )
        maintenances = list(page.maintenances)
        assert len(maintenances) == 1
        assert maintenances[0].id > 0
        assert maintenances[0].title == test_maintenance_title
        assert maintenances[0].start_date == test_maintenance_start_date
        assert maintenances[0].end_date == test_maintenance_end_date
        assert maintenances[0].services == [test_page_service_name]
        assert maintenances[0].page.id == page.id
