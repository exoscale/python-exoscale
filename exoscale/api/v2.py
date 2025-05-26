"""

``exoscale.api.v2`` provides a low-level client targeting Exoscale's
OpenAPI-based V2 API. This client is dynamically generated from the OpenAPI
definition shipped with the package.

Examples:
    Creating a client targeting one of the available zones:

    >>> from exoscale.api.v2 import Client
    >>> c = Client("api-key", "api-secret", zone="de-fra-1")
    >>> c.list_instances()
    {'instances': []}

    Creating a client targeting an endpoint specifically:

    >>> from exoscale.api.v2 import Client
    >>> c = Client("api-key", "api-secret", url="https://api-ch-gva-2.exoscale.com/v2")
    >>> c.list_instances()
    {'instances': []}

    Waiting for an asynchronous operation to complete:

    >>> from exoscale.api.v2 import Client
    >>> c = Client("api-key", "api-secret", zone="ch-gva-2")
    >>> version = c.list_sks_cluster_versions()["sks-cluster-versions"][0]
    >>> operation = c.create_sks_cluster(
    ...     cni="cilium",
    ...     name="my-cluster",
    ...     level="starter",
    ...     version=version,
    ... )
    >>> c.wait(operation["id"])
    {'id': 'e2047130-b86e-11ef-83b3-0d8312b2c2d7',
     'state': 'success',
     'reference': {
         'id': '8561ee34-09f0-42da-a765-abde807f944b',
         'link': '/v2/sks-cluster/8561ee34-09f0-42da-a765-abde807f944b',
         'command': 'get-sks-cluster'}}

    In case of a conflict between argument names and Python keywords, ``**kwargs`` syntax can be used:

    >>> from exoscale.api.v2 import Client
    >>> c = Client("api-key", "api-secret", zone="ch-gva-2")
    >>> c.list_events(**{"from": "2025-03-01"})
    [{'handler': 'authenticate', 'source-ip': 'x.x.x.x', 'message': 'User user@exoscale.com: authenticate', 'status': 200, 'timestamp': '2025-03-10T14:52:34Z'}, {'handler': 'create session', 'source-ip': 'x.x.x.x', 'message': 'User user@exoscale.com: create session', 'status': 200, 'timestamp': '2025-03-10T14:52:46Z'}]
"""

import json
import time
from pathlib import Path

import requests
from exoscale_auth import ExoscaleV2Auth

from .generator import (
    _return_docstring,
    create_client_class,
    ExoscaleAPIClientException,
    ExoscaleAPIServerException,
)


def _poll_interval(run_time):
    """
    Returns the wait interval before next poll, given the current run time of a job.
    We poll
     - every 3 seconds for the first 30 seconds
     - then increase linearly to reach 1 minute at 15 minutes of run time
     - then every minute
    """
    # y = a * x + b. Solve a and b for:
    # 60 = a * 900 + b
    # 3 = a * 30 + b
    a = 57 / 870
    b = 3 - 30 * a
    min_wait = 3
    max_wait = 60
    interval = a * run_time + b
    interval = max(min_wait, interval)
    interval = min(max_wait, interval)
    return interval


def _time():
    return time.time()


def _sleep(start_time):
    run_time = _time() - start_time
    interval = _poll_interval(run_time)
    return time.sleep(interval)


with open(Path(__file__).parent.parent / "openapi.json", "r") as f:
    api_spec = json.load(f)
    BaseClient = create_client_class(api_spec)


class Client(BaseClient):
    def __init__(self, key, secret, *args, url=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.WAIT_ABORT_ERRORS_COUNT = 5

        client = requests.Session()
        client.auth = ExoscaleV2Auth(key, secret)
        self.http_client = client
        self.key = key

    def __repr__(self):
        return (
            f"<Client endpoint={self.endpoint}"
            f" key={self.key} secret=***masked***>"
        )

    def wait(self, operation_id: str, max_wait_time: int = None):
        """
        Wait for completion of an asynchronous operation.

        Args:
            operation_id (str)
            max_wait_time (int): When set, stop waiting after this time in
              seconds. Defaults to ``None``, which waits until operation
              completion.

        Returns:
            {ret}
        """
        start_time = _time()
        subsequent_errors = 0
        while True:
            try:
                result = self.get_operation(id=operation_id)
                subsequent_errors = 0
            except ExoscaleAPIServerException as e:
                subsequent_errors += 1
                if subsequent_errors >= self.WAIT_ABORT_ERRORS_COUNT:
                    raise ExoscaleAPIServerException(
                        "Server error while polling operation"
                    ) from e
                _sleep(start_time)
                continue
            state = result["state"]
            if state == "success":
                return result
            elif state in {"failure", "timeout"}:
                raise ExoscaleAPIServerException(
                    f"Operation error: {state}, {result['reason']}"
                )
            elif state == "pending":
                run_time = _time() - start_time
                if max_wait_time is not None and run_time > max_wait_time:
                    raise ExoscaleAPIClientException(
                        "Operation max wait time reached"
                    )
                _sleep(start_time)
            else:
                raise ExoscaleAPIServerException(
                    f"Invalid operation state: {state}"
                )


Client.wait.__doc__ = Client.wait.__doc__.format(
    ret=_return_docstring(
        Client._api_spec, Client._by_operation["get-operation"]["operation"]
    )
)
