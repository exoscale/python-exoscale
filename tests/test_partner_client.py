"""Tests for Partner API client."""

from unittest.mock import patch

import pytest

from exoscale.api.exceptions import (
    ExoscaleAPIAuthException,
    ExoscaleAPIClientException,
    ExoscaleAPIServerException,
)
from exoscale.api.partner import Client


def test_client_creation():
    """Test Partner API client creation."""
    c = Client("key", "secret")
    assert hasattr(c, "list_distributor_organizations")
    assert hasattr(c, "create_distributor_organization")
    assert c.endpoint == "https://partner-api.exoscale.com/v1.alpha"


def test_client_with_custom_url():
    """Test client with custom URL."""
    c = Client("key", "secret", url="https://custom.example.com/v1")
    assert c.endpoint == "https://custom.example.com/v1"


def test_client_error_handling(requests_mock):
    """Test error handling matches V2 client patterns."""
    client = Client(key="EXOtest", secret="test")

    # Mock a 403 authentication error
    requests_mock.get(
        "https://partner-api.exoscale.com/v1.alpha/distributor/organization",
        status_code=403,
        text='{"message":"Invalid request signature"}',
    )

    with pytest.raises(ExoscaleAPIAuthException) as exc:
        client.list_distributor_organizations()
    assert "Authentication error 403" in str(exc.value)

    # Mock a 404 client error
    requests_mock.get(
        "https://partner-api.exoscale.com/v1.alpha/distributor/organization/123",
        status_code=404,
        text='{"message":"Organization not found"}',
    )

    with pytest.raises(ExoscaleAPIClientException) as exc:
        client.get_distributor_organization(id="123")
    assert "Client error 404" in str(exc.value)

    # Mock a 503 server error
    requests_mock.post(
        "https://partner-api.exoscale.com/v1.alpha/distributor/organization",
        status_code=503,
        text='{"message":"Service temporarily unavailable"}',
    )

    with pytest.raises(ExoscaleAPIServerException) as exc:
        client.create_distributor_organization(
            name="Test Org",
            address="123 Main St",
            city="Test City",
            postcode="12345",
            country="CH",
            owner_email="test@example.com",
        )
    assert "Server error 503" in str(exc.value)


def test_authentication():
    """Test that Partner client reuses V2 authentication."""
    with patch("exoscale.api.partner.V2Client") as mock_v2:
        client = Client("key", "secret")

        mock_v2.assert_called_once_with("key", "secret", url=None)

        assert client.http_client == mock_v2.return_value.http_client
