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
        title (str): a incident title
        start_date (datetime.datetime): the incident start date
        end_date (datetime.datetime): the incident end date
        services ([str]): a list of services impacted by the incident
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
    title = attr.ib(default=None, repr=False)
    services = attr.ib(default=None, repr=False)

    @classmethod
    def from_rs(cls, runstatus, res, page):
        return cls(
            runstatus,
            res,
            id=res["id"],
            page=page,
            state=res["state"],
            status=res["status"],
            start_date=datetime.strptime(res["start_date"], "%Y-%m-%dT%H:%M:%S.%f%z"),
            end_date=datetime.strptime(res["end_date"], "%Y-%m-%dT%H:%M:%S.%f%z")
            if res["end_date"] is not None
            else None,
            title=res["title"],
            services=res["services"],
        )

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

    def add_event(self, description, state=None, status=None):
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

    def update(self, title=None, services=None):
        """
        Update the incident properties.

        Parameters:
            title (str): an incident title
            services ([str]): a list of services impacted by the incident

        Returns:
            None
        """

        json = {}
        if title is not None:
            json["title"] = title
        if services is not None:
            json["services"] = services

        self.runstatus._patch(
            url="/pages/{p}/incidents/{i}".format(p=self.page.name, i=self.id),
            json=json,
        )

        if title is not None:
            self.title = title
        if services is not None:
            self.services = services

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
        title (str): a maintenance title
        description (str): a maintenance description
        services ([str]): a list of services impacted by the maintenance
        start_date (datetime.datetime): a maintenance start date
        end_date (datetime.datetime): a maintenance end date
        status (str): the maintenance status
        page (Page): the page the maintenance belongs to
    """

    runstatus = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    page = attr.ib(repr=False)
    status = attr.ib(repr=False)
    start_date = attr.ib(repr=False)
    end_date = attr.ib(repr=False)
    title = attr.ib(default=None, repr=False)
    description = attr.ib(default=None, repr=False)
    services = attr.ib(default=None, repr=False)

    @classmethod
    def from_rs(cls, runstatus, res, page):
        return cls(
            runstatus,
            res,
            id=res["id"],
            page=page,
            status=res["status"],
            start_date=datetime.strptime(res["start_date"], "%Y-%m-%dT%H:%M:%S%z"),
            end_date=datetime.strptime(res["end_date"], "%Y-%m-%dT%H:%M:%S%z"),
            title=res["title"],
            description=res["description"],
            services=res["services"],
        )

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

    def add_event(self, description, status=None):
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

    def update(
        self,
        title=None,
        description=None,
        start_date=None,
        end_date=None,
        services=None,
    ):
        """
        Update the maintenance properties.

        Parameters:
            title (str): a maintenance title
            description (str): a maintenance description
            services ([str]): a list of services impacted by the maintenance
            start_date (datetime.datetime): a maintenance start date
            end_date (datetime.datetime): a maintenance end date

        Returns:
            None
        """

        json = {}
        if title is not None:
            json["title"] = title
        if description is not None:
            json["description"] = description
        if services is not None:
            json["services"] = services
        if start_date is not None:
            json["start_date"] = start_date.isoformat()
        if end_date is not None:
            json["end_date"] = end_date.isoformat()

        self.runstatus._patch(
            url="/pages/{p}/maintenances/{i}".format(p=self.page.name, i=self.id),
            json=json,
        )

        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if services is not None:
            self.services = services
        if start_date is not None:
            self.start_date = start_date
        if end_date is not None:
            self.end_date = end_date

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
        title (str): a page title
        default_status_message (str): a default "OK" status message
        custom_domain (str): a custom page domain name
        time_zone (str): a time zone

    Note:
        The expected time zone format is the tz database (a.k.a "tzdata" or "Olson"
        database): https://en.wikipedia.org/wiki/Tz_database
    """

    runstatus = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    name = attr.ib()
    title = attr.ib(default=None, repr=False)
    default_status_message = attr.ib(default=None, repr=False)
    custom_domain = attr.ib(default=None, repr=False)
    time_zone = attr.ib(default=None, repr=False)

    @classmethod
    def from_rs(cls, runstatus, res):
        return cls(runstatus, res, id=res["id"], name=res["subdomain"])

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

    def update(
        self,
        title=None,
        default_status_message=None,
        custom_domain=None,
        time_zone=None,
    ):
        """
        Update the page properties.

        Parameters:
            title (str): a page title
            default_status_message (str): a default "OK" status message
            custom_domain (str): a custom page domain name
            time_zone (str): a time zone

        Returns:
            None

        Note:
            The expected time zone format is the tz database (a.k.a "tzdata" or "Olson"
            database): https://en.wikipedia.org/wiki/Tz_database
        """

        json = {}
        if title is not None:
            json["title"] = title
        if default_status_message is not None:
            json["ok_text"] = default_status_message
        if custom_domain is not None:
            json["domain"] = custom_domain
        if time_zone is not None:
            json["time_zone"] = time_zone

        self.runstatus._patch(url="/pages/{p}".format(p=self.name), json=json)

        if title is not None:
            self.title = title
        if default_status_message is not None:
            self.default_status_message = default_status_message
        if custom_domain is not None:
            self.custom_domain = custom_domain
        if time_zone is not None:
            self.time_zone = time_zone

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
