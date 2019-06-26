# -*- coding: utf-8 -*-

"""
Note:
    This module is not intended for standalone use, please use the :code:`exoscale`
    module or the :code:`exoscale.api.*` submodules.
"""


import attr
import pkg_resources
import platform
import requests
import sys
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.utils import default_user_agent as requests_user_agent


@attr.s
class API(object):
    """
    An Exoscale API client.

    Attributes:
        endpoint (str): the API endpoint
        key (str): the API key
        secret (str): the API secret
        trace (bool): API request/response tracing flag
    """

    endpoint = attr.ib()
    key = attr.ib()
    secret = attr.ib(repr=False)
    trace = attr.ib(default=False, repr=False)

    # HTTP session-related settings
    max_retry = attr.ib(default=3)
    retry_backoff_factor = attr.ib(default=0.3)

    user_agent = (
        "Exoscale-Python/{python_exoscale_version} "
        "cs/{cs_version} "
        "{requests_user_agent} "
        "{python_implementation}/{python_version} "
        "{os_name}/{os_version}"
    ).format(
        python_exoscale_version=pkg_resources.get_distribution("exoscale").version,
        cs_version=pkg_resources.get_distribution("cs").version,
        requests_user_agent=requests_user_agent(),
        python_implementation=platform.python_implementation(),
        python_version=platform.python_version(),
        os_name=platform.system(),
        os_version=platform.release(),
    )

    def send(self, **kwargs):
        """
        Send a signed HTTP request to the API.

        Parameters:
            **kwargs: requests.Request parameters

        Returns:
            request.Response: the HTTP request response
        """

        adapter = HTTPAdapter(
            max_retries=Retry(
                total=self.max_retry,
                backoff_factor=self.retry_backoff_factor,
                status_forcelist=None,
            )
        )

        session = requests.Session()
        session.mount("http://", adapter=adapter)
        session.mount("https://", adapter=adapter)

        req = requests.Request(**kwargs).prepare()
        req.headers.update({"User-Agent": self.user_agent})

        if self.trace:
            print(
                ">>> {method} {url}".format(method=req.method, url=req.url),
                file=sys.stderr,
            )
            print("    headers:{headers}".format(headers=req.headers), file=sys.stderr)
            if req.body:
                print("    body:{body}".format(body=req.body), file=sys.stderr)

        res = session.send(req)

        if self.trace:
            print(
                "<<< {status} {reason}".format(
                    status=res.status_code, reason=res.reason
                ),
                file=sys.stderr,
            )
            print("    headers:{headers}".format(headers=res.headers), file=sys.stderr)
            print("    body:{body}".format(body=res.text), file=sys.stderr)

        return res


@attr.s
class Resource(object):
    """
    A resource returned by the Exoscale API.
    """

    res = attr.ib(repr=False)


@attr.s
class APIException(Exception):
    """
    A generic API error.
    """

    reason = attr.ib()
    error = attr.ib(default=None, repr=False)


@attr.s
class RequestError(Exception):
    """
    An API request error.
    """

    reason = attr.ib()
    error = attr.ib(default=None, repr=False)


class ResourceNotFoundError(APIException):
    """
    An error indicating that requested resource cannot be found.
    """

    def __init__(self):
        super().__init__("resource not found")

    def __repr__(self):
        return self.reason

    def __str__(self):
        return self.__repr__()
