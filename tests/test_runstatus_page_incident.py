#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.runstatus import *
from datetime import timezone


class TestRunstatusPageIncident:
    def test_update(self, exo, runstatus_page):
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

        exo.runstatus._post(
            url="/pages/{p}/incidents".format(p=page.name),
            json={
                "title": test_incident_title,
                "status_text": test_incident_description,
                "status": test_incident_status,
                "state": test_incident_state,
                "services": test_incident_services,
            },
        )

        res = exo.runstatus._get(url="/pages/{p}/incidents".format(p=page.name)).json()
        incident = Incident.from_rs(exo.runstatus, res["results"][0], page)

        incident.update(description="Hmm...", status="investigating")
        incident.update(description="Who did this?!", status="identified")
        incident.update(
            description="Should be better now",
            status="monitoring",
            state="degraded_performance",
        )

        res = exo.runstatus._get(
            url="/pages/{p}/incidents/{i}/events".format(p=page.name, i=incident.id)
        ).json()
        assert len(res["results"]) == 4
        assert res["results"][0]["text"] == "Should be better now"
        assert res["results"][0]["state"] == "degraded_performance"
        assert res["results"][0]["status"] == "monitoring"
        assert res["results"][1]["text"] == "Who did this?!"
        assert res["results"][1]["state"] == "major_outage"
        assert res["results"][1]["status"] == "identified"
        assert res["results"][2]["text"] == "Hmm..."
        assert res["results"][2]["state"] == "major_outage"
        assert res["results"][2]["status"] == "investigating"

    def test_close(self, exo, runstatus_page):
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

        exo.runstatus._post(
            url="/pages/{p}/incidents".format(p=page.name),
            json={
                "title": test_incident_title,
                "status_text": test_incident_description,
                "status": test_incident_status,
                "state": test_incident_state,
                "services": test_incident_services,
            },
        )

        res = exo.runstatus._get(url="/pages/{p}/incidents".format(p=page.name)).json()
        incident = Incident.from_rs(exo.runstatus, res["results"][0], page)

        incident.close(description="There, I fixed it")

        res = exo.runstatus._get(
            url="/pages/{p}/incidents/{i}/events".format(p=page.name, i=incident.id)
        ).json()
        assert len(res["results"]) == 2
        assert res["results"][0]["text"] == "There, I fixed it"
        assert res["results"][0]["state"] == "operational"
        assert res["results"][0]["status"] == "resolved"

    def test_properties(self, exo, runstatus_page):
        page = Page.from_rs(exo.runstatus, runstatus_page())
        test_incident_title = "Everything's on fire"
        test_incident_title_edited = "Everything's on fire (edited)"
        test_incident_description = "It's fine ¯\\_(ツ)_/¯"
        test_incident_state = "major_outage"
        test_incident_status = "identified"
        test_incident_services = ["a", "b", "c"]

        for i in test_incident_services:
            exo.runstatus._post(
                url="/pages/{p}/services".format(p=page.name), json={"name": i}
            )

        exo.runstatus._post(
            url="/pages/{p}/incidents".format(p=page.name),
            json={
                "title": test_incident_title,
                "status_text": test_incident_description,
                "status": test_incident_status,
                "state": test_incident_state,
                "services": test_incident_services,
            },
        )

        res = exo.runstatus._get(url="/pages/{p}/incidents".format(p=page.name)).json()
        incident = Incident.from_rs(exo.runstatus, res["results"][0], page)

        incident.title = test_incident_title_edited
        assert incident.title == test_incident_title_edited

        incident.services = ["a"]
        assert incident.services == ["a"]

        for i in [1, 2, 3]:
            exo.runstatus._post(
                url="/pages/{p}/incidents/{i}/events".format(
                    p=page.name, i=incident.id
                ),
                json={
                    "text": "Update #{}".format(i),
                    "status": incident.status,
                    "state": incident.state,
                },
            )

        incident_events = list(incident.events)
        assert len(incident_events) == 4
        assert incident_events[0].description == "Update #3"
        assert incident_events[1].description == "Update #2"
        assert incident_events[2].description == "Update #1"
