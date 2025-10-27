"""
Exoscale Partner API client

This module provides a client for the Exoscale Partner API, which allows
distributors to manage sub-organizations.
"""

import json
from pathlib import Path

from .generator import create_client_class
from .v2 import Client as V2Client


with open(Path(__file__).parent.parent / "partner-api.json", "r") as f:
    partner_api_spec = json.load(f)
    BasePartnerClient = create_client_class(partner_api_spec)


class Client(BasePartnerClient):
    """
    Partner API client with Exoscale authentication.

    This client provides access to distributor operations for managing
    sub-organizations. It uses the same authentication mechanism as the
    V2 API client.

    Args:
        key (str): Exoscale API key
        secret (str): Exoscale API secret
        url (str): Override endpoint URL (optional)
        zone (str): Exoscale zone (optional)

    Example:
        >>> from exoscale.api.partner import Client
        >>> client = Client("EXO...", "secret")
        >>> orgs = client.list_distributor_organizations()
    """

    def __init__(self, key, secret, *args, url=None, **kwargs):
        # Initialize with Partner API endpoint
        partner_url = (
            url if url else "https://partner-api.exoscale.com/v1.alpha"
        )
        super().__init__(*args, url=partner_url, **kwargs)

        # Reuse the v2 client's authentication mechanism
        v2_client = V2Client(key, secret, *args, url=url, **kwargs)

        self.http_client = v2_client.http_client
        self.key = key

        self._v2_client = v2_client

    def __repr__(self):
        return (
            f"<Client endpoint={self.endpoint} "
            f"key={self.key} secret=**masked**>"
        )
