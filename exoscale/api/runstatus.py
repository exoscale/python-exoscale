# -*- coding: utf-8 -*-

"""
This submodule represents the Exoscale Runstatus API.
"""

import attr
from datetime import datetime
from exoscale_auth import ExoscaleAuth
from . import API, Resource, APIException, RequestError, ResourceNotFoundError

_SUPPORTED_INCIDENT_STATES = {"major_outage", "partial_outage", "degraded_performance"}
_SUPPORTED_INCIDENT_STATUSES = {"investigating", "identified", "monitoring"}
_SUPPORTED_MAINTENANCE_STATUSES = {"scheduled", "in-progress"}


@attr.s
class Service(Resource):
    """
    A Runstatus service.

    Attributes:
        id (int): the service unique identifier
        name (str): the service name
        page (Page): the page the incident belongs to
    """

    runstatus = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    name = attr.ib()
    page = attr.ib(repr=False)

    @classmethod
    def from_rs(cls, runstatus, res, page):
        return cls(
            runstatus, res, id=res["url"].split("/")[-1], name=res["name"], page=page
        )

    @property
    def state(self):
        """
        Service state.

        Returns:
            str: the service state
        """

        if "state" in self.res:
            return self.res["state"]

        res = self.runstatus._get(
            url="/pages/{p}/services/{s}".format(p=self.page.name, s=self.id)
        )

        return res["state"]

    def delete(self):
        """
        Delete the service.

        Returns:
            None
        """

        self.runstatus._delete(
            url="/pages/{p}/services/{s}".format(p=self.page.name, s=self.id)
        )

        self.runstatus = None
        self.res = None
        self.id = None
        self.name = None
        self.page = None


@attr.s
class IncidentEvent(Resource):
    """
    A Runstatus incident event.

    Attributes:
        date (datetime.datetime): the event date
        description (str): the event description
        status (str): the target status for the incident
        state (str): the target state for the services impacted
        incident (Incident): the incident the event belongs to
    """

    runstatus = attr.ib(repr=False)
    res = attr.ib(repr=False)
    date = attr.ib(repr=False)
    description = attr.ib(repr=False)
    status = attr.ib(repr=False)
    state = attr.ib(repr=False)
    incident = attr.ib(repr=False)


@attr.s
class Incident(Resource):
    """
    A Runstatus incident.

    Attributes:
        id (int): the incident unique identifier
        start_date (datetime.datetime): the incident start date
        end_date (datetime.datetime): the incident end date
        state (str): the incident state
        status (str): the incident status
        page (Page): the page the incident belongs to
    """

    runstatus = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    page = attr.ib(repr=False)
    state = attr.ib(repr=False)
    status = attr.ib(repr=False)
    start_date = attr.ib(repr=False)
    end_date = attr.ib(default=None, repr=False)

    @classmethod
    def from_rs(cls, runstatus, res, page):
        return cls(
            runstatus,
            res,
            id=res["id"],
            start_date=datetime.strptime(res["start_date"], "%Y-%m-%dT%H:%M:%S.%f%z"),
            end_date=datetime.strptime(res["end_date"], "%Y-%m-%dT%H:%M:%S.%f%z")
            if res["end_date"] is not None
            else None,
            state=res["state"],
            status=res["status"],
            page=page,
        )

    @property
    def title(self):
        """
        Incident title.

        Returns:
            str: the incident title
        """

        if "title" in self.res:
            return self.res["title"]

        res = self.runstatus._get(
            url="/pages/{p}/incidents/{i}".format(p=self.name, i=self.id)
        )

        return res["title"]

    @title.setter
    def title(self, title):
        """
        Set the incident title.

        Parameters:
            title (str): the incident title

        Returns:
            None
        """

        self.runstatus._patch(
            url="/pages/{p}/incidents/{i}".format(p=self.page.name, i=self.id),
            json={"title": title},
        )

        self.res["title"] = title

    @property
    def services(self):
        """
        Services impacted by the incident.

        Returns:
            [str]: list of service names
        """

        if "services" in self.res:
            return self.res["services"]

        res = self.runstatus._get(
            url="/pages/{p}/incidents/{i}".format(p=self.name, i=self.id)
        )

        return res["services"]

    @services.setter
    def services(self, services):
        """
        Set the services impacted by the incident.

        Parameters:
            [str]: list of service names

        Returns:
            None
        """

        self.runstatus._patch(
            url="/pages/{p}/incidents/{i}".format(p=self.page.name, i=self.id),
            json={"services": services},
        )

        self.res["services"] = services

    @property
    def events(self):
        """
        Incident event stream.

        Yields:
            IncidentEvent: the next incident event
        """

        res = self.runstatus._get(
            url="/pages/{p}/incidents/{i}/events".format(p=self.page.name, i=self.id)
        )

        for i in res.json().get("results", []):
            yield IncidentEvent(
                self.runstatus,
                i,
                date=datetime.strptime(i["created"], "%Y-%m-%dT%H:%M:%S.%f%z"),
                description=i["text"],
                status=i["status"],
                state=i["state"],
                incident=self,
            )

    def update(self, description, state=None, status=None):
        """
        Update the incident event stream.

        Parameters:
            description (str): the event description
            state (str): a new incident state to set
            status (str): a new incident status to set

        Returns:
            None
        """

        if state is not None and state not in _SUPPORTED_INCIDENT_STATES:
            raise ValueError(
                "unsupported state; supported states are: {}".format(
                    ",".join(_SUPPORTED_INCIDENT_STATES)
                )
            )

        if status is not None and status not in _SUPPORTED_INCIDENT_STATUSES:
            raise ValueError(
                "unsupported status; supported statuses are: {}".format(
                    ",".join(_SUPPORTED_INCIDENT_STATUSES)
                )
            )

        self.runstatus._post(
            url="/pages/{p}/incidents/{i}/events".format(p=self.page.name, i=self.id),
            json={
                "text": description,
                "status": status if status is not None else self.status,
                "state": state if state is not None else self.state,
            },
        )

        self.state = state if state is not None else self.state
        self.status = status if status is not None else self.status

    def close(self, description):
        """
        Close the incident.

        Parameters:
            description (str): the incident closing description

        Returns:
            None
        """

        self.runstatus._post(
            url="/pages/{p}/incidents/{i}/events".format(p=self.page.name, i=self.id),
            json={"text": description, "status": "resolved", "state": "operational"},
        )


@attr.s
class MaintenanceEvent(Resource):
    """
    A Runstatus maintenance event.

    Attributes:
        date (datetime.datetime): the event date
        description (str): the event description
        status (str): the target status for the maintenance
        maintenance (Maintenance): the maintenance the event belongs to
    """

    runstatus = attr.ib(repr=False)
    res = attr.ib(repr=False)
    date = attr.ib(repr=False)
    description = attr.ib(repr=False)
    status = attr.ib(repr=False)
    maintenance = attr.ib(repr=False)


@attr.s
class Maintenance(Resource):
    """
    A Runstatus maintenance.

    Attributes:
        id (int): the maintenance unique identifier
        status (str): the maintenance status
        page (Page): the page the maintenance belongs to
    """

    runstatus = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    status = attr.ib(repr=False)
    page = attr.ib(repr=False)

    @classmethod
    def from_rs(cls, runstatus, res, page):
        return cls(runstatus, res, id=res["id"], status=res["status"], page=page)

    @property
    def title(self):
        """
        Maintenance title.

        Returns:
            str: the maintenance title.
        """

        if "title" in self.res:
            return self.res["title"]

        res = self.runstatus._get(
            url="/pages/{p}/maintenance/{m}".format(p=self.name, m=self.id)
        )

        return res["title"]

    @title.setter
    def title(self, title):
        """
        Set the maintenance title.

        Parameters:
            title (str): the maintenance title

        Returns:
            None
        """

        self.runstatus._patch(
            url="/pages/{p}/maintenances/{m}".format(p=self.page.name, m=self.id),
            json={"title": title},
        )

        self.res["title"] = title

    @property
    def description(self):
        """
        Maintenance description.

        Returns:
            str: the maintenance description
        """

        if "description" in self.res:
            return self.res["description"]

        res = self.runstatus._get(
            url="/pages/{p}/maintenance/{m}".format(p=self.name, m=self.id)
        )

        return res["description"]

    @description.setter
    def description(self, description):
        """
        Set the maintenance description.

        Parameters:
            description (str): the maintenance description

        Returns:
            None
        """

        self.runstatus._patch(
            url="/pages/{p}/maintenances/{m}".format(p=self.page.name, m=self.id),
            json={"description": description},
        )

        self.res["description"] = description

    @property
    def start_date(self):
        """
        Maintenance start date.

        Returns:
            datetime.datetime: the maintenance start date
        """

        if "start_date" in self.res:
            return datetime.strptime(self.res["start_date"], "%Y-%m-%dT%H:%M:%S%z")

        res = self.runstatus._get(
            url="/pages/{p}/maintenance/{m}".format(p=self.name, m=self.id)
        )

        return datetime.strptime(res["start_date"], "%Y-%m-%dT%H:%M:%S%z")

    @start_date.setter
    def start_date(self, date):
        """
        Set the maintenance start date.

        Parameters:
            date (datetime.datetime): the maintenance start date

        Returns:
            None
        """

        self.runstatus._patch(
            url="/pages/{p}/maintenances/{m}".format(p=self.page.name, m=self.id),
            json={"start_date": date.isoformat()},
        )

        self.res["start_date"] = date.isoformat()

    @property
    def end_date(self):
        """
        Maintenance end date.

        Returns:
            datetime.datetime: the maintenance end date
        """

        if "end_date" in self.res:
            return datetime.strptime(self.res["end_date"], "%Y-%m-%dT%H:%M:%S%z")

        res = self.runstatus._get(
            url="/pages/{p}/maintenance/{m}".format(p=self.name, m=self.id)
        )

        return datetime.strptime(res["end_date"], "%Y-%m-%dT%H:%M:%S%z")

    @end_date.setter
    def end_date(self, date):
        """
        Set the maintenance end date.

        Parameters:
            date (datetime.datetime): the maintenance end date

        Returns:
            None
        """

        self.runstatus._patch(
            url="/pages/{p}/maintenances/{m}".format(p=self.page.name, m=self.id),
            json={"end_date": date.isoformat()},
        )

        self.res["end_date"] = date.isoformat()

    @property
    def services(self):
        """
        Services impacted by the maintenance.

        Returns:
            [str]: list of service names
        """

        if "services" in self.res:
            return self.res["services"]

        res = self.runstatus._get(
            url="/pages/{p}/maintenance/{m}".format(p=self.name, m=self.id)
        )

        return res["services"]

    @services.setter
    def services(self, services):
        """
        Set the services impacted by the maintenance.

        Parameters:
            services ([str]): list of service names

        Returns:
            None
        """

        self.runstatus._patch(
            url="/pages/{p}/maintenances/{m}".format(p=self.page.name, m=self.id),
            json={"services": services},
        )

        self.res["services"] = services

    @property
    def events(self):
        """
        Maintenance event stream.

        Yields:
            MaintenanceEvent: the next maintenance event
        """

        res = self.runstatus._get(
            url="/pages/{p}/maintenances/{m}/events".format(p=self.page.name, m=self.id)
        )

        for i in res.json().get("results", []):
            yield MaintenanceEvent(
                self.runstatus,
                i,
                date=datetime.strptime(i["created"], "%Y-%m-%dT%H:%M:%S.%f%z"),
                description=i["text"],
                status=i["status"],
                maintenance=self,
            )

    def update(self, description, status=None):
        """
        Update the maintenance event stream.

        Parameters:
            description (str): the event description
            status (str): a new maintenance status to set

        Returns:
            None
        """

        if status is not None and status not in _SUPPORTED_MAINTENANCE_STATUSES:
            raise ValueError(
                "unsupported status; supported statuses are: {}".format(
                    ",".join(_SUPPORTED_MAINTENANCE_STATUSES)
                )
            )

        self.runstatus._post(
            url="/pages/{p}/maintenances/{m}/events".format(
                p=self.page.name, m=self.id
            ),
            json={
                "text": description,
                "status": status if status is not None else self.status,
            },
        )

        self.status = status if status is not None else self.status

    def close(self, description):
        """
        Close the maintenance.

        Parameters:
            description (str): the maintenance closing description

        Returns:
            None
        """

        self.runstatus._post(
            url="/pages/{p}/maintenances/{m}/events".format(
                p=self.page.name, m=self.id
            ),
            json={"text": description, "status": "completed"},
        )


@attr.s
class Page(Resource):
    """
    A Runstatus page.

    Attributes:
        id (int): the page unique identifier
        name (str): the page name
    """

    runstatus = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    name = attr.ib()

    @classmethod
    def from_rs(cls, runstatus, res):
        return cls(runstatus, res, id=res["id"], name=res["subdomain"])

    @property
    def title(self):
        """
        Page title.

        Returns:
            str: the page title
        """

        if "title" in self.res:
            return self.res["title"]

        res = self.runstatus._get(url="/pages/{p}".format(p=self.name))

        return res["title"]

    @title.setter
    def title(self, title):
        """
        Set the page title.

        Parameters:
            title (str): the page title

        Returns:
            None
        """

        self.runstatus._patch(
            url="/pages/{p}".format(p=self.name), json={"title": title}
        )

        self.res["title"] = title

    @property
    def default_status_message(self):
        """
        Page default status message.

        Returns:
            str: the page default status message
        """

        if "ok_text" in self.res:
            return self.res["ok_text"]

        res = self.runstatus._get(url="/pages/{p}".format(p=self.name))

        return res["ok_text"]

    @default_status_message.setter
    def default_status_message(self, message):
        """
        Set the page default status message.

        Parameters:
            message (str): the page default status message
        """

        self.runstatus._patch(
            url="/pages/{p}".format(p=self.name), json={"ok_text": message}
        )

        self.res["ok_text"] = message

    @property
    def custom_domain(self):
        """
        Custom page domain name.

        Returns:
            str: the page custom domain name
        """

        if "domain" in self.res:
            return self.res["domain"]

        res = self.runstatus._get(url="/pages/{p}".format(p=self.name))

        return res["domain"]

    @custom_domain.setter
    def custom_domain(self, domain):
        """
        Set a custom page domain name.

        Parameters:
            domain (str): the custom page domain name
        """

        self.runstatus._patch(
            url="/pages/{p}".format(p=self.name), json={"domain": domain}
        )

        self.res["domain"] = domain

    @property
    def time_zone(self):
        """
        Page time zone.

        Returns:
            str: the page time zone
        """

        if "time_zone" in self.res:
            return self.res["time_zone"]

        res = self.runstatus._get(url="/pages/{p}".format(p=self.name))

        return res["time_zone"]

    @time_zone.setter
    def time_zone(self, tz):
        """
        Set a page time zone.

        Parameters:
            tz (str): a time zone

        Returns:
            None

        Note:
            The expected time zone format is the tz database (a.k.a "tzdata" or "Olson"
            database): https://en.wikipedia.org/wiki/Tz_database
        """

        self.runstatus._patch(
            url="/pages/{p}".format(p=self.name), json={"time_zone": tz}
        )

        self.res["time_zone"] = tz

    @property
    def services(self):
        """
        Page services.

        Yields:
            Service: the next service
        """

        res = self.runstatus._get(url="/pages/{p}/services".format(p=self.name))

        for i in res.json().get("results", []):
            yield Service.from_rs(self.runstatus, i, page=self)

    def add_service(self, name):
        """
        Add a service to the page.

        Parameters:
            name (str): the name of the service
        
        Returns:
            None
        """

        self.runstatus._post(
            url="/pages/{p}/services".format(p=self.name), json={"name": name}
        )

    @property
    def incidents(self):
        """
        Page incidents.

        Yields:
            Incident: the next incident
        """

        res = self.runstatus._get(url="/pages/{p}/incidents".format(p=self.name))

        for i in res.json().get("results", []):
            yield Incident.from_rs(self.runstatus, i, self)

    def add_incident(self, title, description, state, status, services=None):
        """
        Open a new incident.

        Parameters:
            title (str): the incident title
            description (str): the incident description
            state (str): the incident state
            status (str): the incident status
            services ([str]): the names of services impacted by the incident

        Returns:
            None
        """

        if services is None:
            services = []

        if state not in _SUPPORTED_INCIDENT_STATES:
            raise ValueError(
                "unsupported state; supported states are: {}".format(
                    ",".join(_SUPPORTED_INCIDENT_STATES)
                )
            )

        if status not in _SUPPORTED_INCIDENT_STATUSES:
            raise ValueError(
                "unsupported status; supported statuses are: {}".format(
                    ",".join(_SUPPORTED_INCIDENT_STATUSES)
                )
            )

        self.runstatus._post(
            url="/pages/{p}/incidents".format(p=self.name),
            json={
                "title": title,
                "status_text": description,
                "status": status,
                "state": state,
                "services": services,
            },
        )

    @property
    def maintenances(self):
        """
        Page maintenance.

        Yields:
            Maintenance: the next maintenance
        """

        res = self.runstatus._get(url="/pages/{p}/maintenances".format(p=self.name))

        for i in res.json().get("results", []):
            yield Maintenance.from_rs(self.runstatus, i, self)

    def add_maintenance(self, title, description, start_date, end_date, services=None):
        """
        Open a new maintenance.

        Parameters:
            title (str): the maintenance title
            description (str): the maintenance description
            start_date (datetime.datetime): the maintenance start date
            end_date (datetime.datetime): the maintenance end date
            services ([str]): the names of services impacted by the maintenance

        Returns:
            None
        """

        if services is None:
            services = []

        self.runstatus._post(
            url="/pages/{p}/maintenances".format(p=self.name),
            json={
                "title": title,
                "description": description,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "services": services,
            },
        )

    def delete(self):
        """
        Delete the page.

        Returns:
            None
        """

        self.runstatus._delete(url="/pages/{p}".format(p=self.name))

        self.runstatus = None
        self.res = None
        self.id = None
        self.name = None


class RunstatusAPI(API):
    """
    An Exoscale Runstatus API client.

    Parameters:
        key (str): the Runstatus API key
        secret (str): the Runstatus API secret
        endpoint (str): the Runstatus API endpoint
        trace (bool): API request/response tracing flag
    """

    def __init__(self, key, secret, endpoint=None, trace=False):
        endpoint = "https://api.runstatus.com" if endpoint is None else endpoint
        super().__init__(endpoint, key, secret, trace)

        self.auth = ExoscaleAuth(self.key, self.secret)

    def __repr__(self):
        return "RunstatusAPI(endpoint='{}' key='{}')".format(self.endpoint, self.key)

    def __str__(self):
        return self.__repr__()

    def _check_api_response(self, res, *args, **kwargs):
        """
        Check the API response and raise an exception depending on the status code.
        """

        if res.status_code >= 500:
            raise APIException(res.text)

        if res.status_code == 404:
            raise ResourceNotFoundError

        if res.status_code >= 400:
            raise RequestError(str(res.text))

    def _send(self, **kwargs):
        """
        Send a free-form HTTP request.

        Parameters:
            kwargs: request.Request parameters

        Returns:
            request.Response: the HTTP response
        """

        return API.send(
            self, auth=self.auth, hooks={"response": self._check_api_response}, **kwargs
        )

    def _get(self, url, **kwargs):
        """
        Send an HTTP GET request to the Runstatus API.

        Parameters:
            url (str): the URL to request
            kwargs: request.Request parameters

        Returns:
            request.Response: the HTTP response received from the Runstatus API
        """

        return self._send(
            method="GET", url=self.endpoint + "/" + url.lstrip("/"), **kwargs
        )

    def _post(self, url, json, **kwargs):
        """
        Send an HTTP POST request to the Runstatus API.

        Parameters:
            url (str): the URL to request
            json (dict): the dict of parameters to send in JSON-formatted payload
            kwargs: request.Request parameters

        Returns:
            request.Response: the HTTP response received from the Runstatus API
        """

        return self._send(
            method="POST",
            url=self.endpoint + "/" + url.lstrip("/"),
            json=json,
            **kwargs
        )

    def _patch(self, url, json, **kwargs):
        """
        Send an HTTP PATCH request to the Runstatus API.

        Parameters:
            url (str): the URL to request
            json (dict): the dict of parameters to send in JSON-formatted payload
            kwargs: request.Request parameters

        Returns:
            request.Response: the HTTP response received from the Runstatus API
        """

        return self._send(
            method="PATCH",
            url=self.endpoint + "/" + url.lstrip("/"),
            json=json,
            **kwargs
        )

    def _delete(self, url, **kwargs):
        """
        Send an HTTP DELETE request to the Runstatus API.

        Parameters:
            url (str): the URL to request
            kwargs: request.Request parameters

        Returns:
            request.Response: the HTTP response received from the Runstatus API
        """

        return self._send(
            method="DELETE", url=self.endpoint + "/" + url.lstrip("/"), **kwargs
        )

    ## Page

    def create_page(self, name):
        """
        Create a Runstatus page.

        Parameters:
            name (str): the page name

        Returns:
            Page: the Runstatus page created
        """

        res = self._post(url="/pages", json={"name": name, "subdomain": name})

        return Page.from_rs(self, res.json())

    def list_pages(self):
        """
        List Runstatus pages.

        Yields:
            Page: the next Runstatus page
        """

        res = self._get(url="/pages")

        for i in res.json().get("results", []):
            yield Page.from_rs(self, i)

    def get_page(self, name=None, id=None):
        """
        Get a Runstatus page.

        Parameters:
            name (str): a Runstatus page name
            id (int): a Runstatus page unique identifier

        Returns:
            Page: a Runstatus page
        """

        if id is None and name is None:
            raise ValueError("either id or name must be specifed")

        pages = self.list_pages()

        for page in pages:
            if (name and page.name == name) or (id and page.id == id):
                return page

        raise ResourceNotFoundError
