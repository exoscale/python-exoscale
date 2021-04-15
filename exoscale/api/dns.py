# -*- coding: utf-8 -*-

"""
This submodule represents the Exoscale DNS API.
"""

import attr
from . import API, Resource, APIException, ResourceNotFoundError
from cs import CloudStack, CloudStackApiException

_SUPPORTED_RECORD_TYPES = {
    "A",
    "AAAA",
    "ALIAS",
    "CAA",
    "CNAME",
    "DNSKEY",
    "DS",
    "HINFO",
    "MX",
    "NAPTR",
    "NS",
    "POOL",
    "PTR",
    "SOA",
    "SPF",
    "SRV",
    "SSHFP",
    "TXT",
    "URL",
}


@attr.s
class Domain(Resource):
    """
    A DNS domain.

    Attributes:
        id (int): the DNS domain unique identifier
        name (str): the DNS domain name
    """

    dns = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    name = attr.ib()
    unicode_name = attr.ib(repr=False)

    @classmethod
    def _from_cs(cls, dns, res):
        return cls(
            dns, res, id=res["id"], name=res["name"], unicode_name=res["unicodename"]
        )

    @property
    def records(self):
        """
        Domain records.

        Yields:
            DomainRecord: the next DNS domain record defined

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            _list = self.dns.cs.listDnsDomainRecords(id=self.id, fetch_list=True)
            for i in _list:
                yield DomainRecord._from_cs(self.dns, domain=self, res=i)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def add_record(self, name, type, content, priority=None, ttl=3600):
        """
        Add a record to the DNS domain.

        Parameters:
            name (str): the DNS domain record name
            type (str): the DNS domain record type
            content (str): the DNS domain record content
            priority (int): the DNS domain record priority
            ttl (int): the DNS domain record TTL

        Returns:
            None
        """

        if type not in _SUPPORTED_RECORD_TYPES:
            raise ValueError(
                "unsupported record type; supported types are: {}".format(
                    ",".join(_SUPPORTED_RECORD_TYPES)
                )
            )

        try:
            self.dns.cs.createDnsDomainRecord(
                name=self.name,
                record_name=name,
                record_type=type,
                content=content,
                priority=priority,
                ttl=ttl,
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def delete(self):
        """
        Delete the DNS domain.

        Returns:
            None
        """

        try:
            self.dns.cs.deleteDnsDomain(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self._reset()


@attr.s
class DomainRecord(Resource):
    """
    A DNS domain record.

    Attributes:
        id (int): the DNS domain record unique identifier
        domain (Domain): the DNS domain the record belongs to
        type (str): the DNS domain record type
        name (str): the DNS domain record name
        content (str): the DNS domain record content
        priority (int): the DNS domain record priority
        ttl (int): the DNS domain record TTL
    """

    dns = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    domain = attr.ib(repr=False)
    type = attr.ib()
    name = attr.ib(repr=False)
    content = attr.ib(repr=False)
    priority = attr.ib(default=None, repr=False)
    ttl = attr.ib(default=3600, repr=False)

    @classmethod
    def _from_cs(cls, dns, res, domain):
        return cls(
            dns,
            res,
            domain=domain,
            id=res["id"],
            type=res["record_type"],
            name=res["name"],
            content=res["content"],
            priority=res.get("priority"),
            ttl=res["ttl"],
        )

    def update(self, name=None, content=None, priority=None, ttl=3600):
        """
        Update a DNS domain record.

        Parameters:
            name (str): the DNS domain record name
            content (str): the DNS domain record content
            priority (int): the DNS domain record priority
            ttl (int): the DNS domain record TTL

        Returns:
            None
        """

        try:
            self.dns.cs.updateDnsDomainRecord(
                name=self.domain.name,
                record_id=self.id,
                record_type=self.type,
                record_name=name if name else self.name,
                content=content if content else self.content,
                priority=priority if priority else self.priority,
                ttl=ttl if ttl else self.ttl,
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.name = name if name else self.name
        self.content = content if content else self.content
        self.priority = priority if priority else self.priority
        self.ttl = ttl if ttl else self.ttl

    def delete(self):
        """
        Delete the DNS domain record.

        Returns:
            None
        """

        try:
            self.dns.cs.deleteDnsDomainRecord(id=self.domain.id, record_id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self._reset()


class DnsAPI(API):
    """
    An Exoscale DNS API client.

    Parameters:
        key (str): the DNS API key
        secret (str): the DNS API secret
        endpoint (str): the DNS API endpoint
        max_retries (int): the API HTTP session retry policy number of retries to allow
        trace (bool): API request/response tracing flag
    """

    def __init__(
        self,
        key,
        secret,
        endpoint="https://api.exoscale.com/v1",
        max_retries=None,
        trace=False,
    ):
        super().__init__(
            endpoint=endpoint,
            key=key,
            secret=secret,
            max_retries=max_retries,
            trace=trace,
        )

        self.cs = CloudStack(
            key=key,
            secret=secret,
            endpoint=endpoint,
            session=self.session,
            headers={**self.session.headers, **{"User-Agent": self.user_agent}},
            trace=self.trace,
            fetch_result=True,
        )

    def __repr__(self):
        return "DnsAPI(endpoint='{}' key='{}')".format(self.endpoint, self.key)

    def __str__(self):
        return self.__repr__()

    ### Domain

    def create_domain(self, name):
        """
        Create a DNS domain.

        Parameters:
            name (str): the domain name

        Returns:
            Domain: the DNS domain created
        """

        try:
            res = self.cs.createDnsDomain(name=name)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return Domain._from_cs(self, res["dnsdomain"])

    def list_domains(self):
        """
        List DNS domains.

        Yields:
            Domain: the next DNS domain
        """

        try:
            _list = self.cs.listDnsDomains(fetch_list=True)

            for i in _list:
                yield Domain._from_cs(self, i)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def get_domain(self, name=None, id=None):
        """
        Get a DNS domain.

        Parameters:
            id (str): a DNS domain identifier
            name (str): a DNS domain name

        Returns:
            Domain: a DNS domain
        """

        if id is None and name is None:
            raise ValueError("either id or name must be specifed")

        try:
            domains = self.list_domains()
        except APIException as e:
            if "does not exist" in e.error["errortext"]:
                raise ResourceNotFoundError
            raise

        for domain in domains:
            if (name and domain.name == name) or (id and domain.id == id):
                return domain

        raise ResourceNotFoundError
