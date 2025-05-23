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
from pathlib import Path

from .generator import create_client_class


with open(Path(__file__).parent.parent / "openapi.json", "r") as f:
    api_spec = json.load(f)
    Client = create_client_class(api_spec)
