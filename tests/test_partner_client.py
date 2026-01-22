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
            display_name="Test Org",
            billing_address={
                "name": "Test Organization",
                "street-name": "Main Street",
                "building-number": "123",
                "city": "Test City",
                "postal-code": "12345",
                "country": "CH",
            },
            owner_email="test@example.com",
        )
    assert "Server error 503" in str(exc.value)


def test_authentication():
    """Test that Partner client reuses V2 authentication."""
    with patch("exoscale.api.partner.V2Client") as mock_v2:
        client = Client("key", "secret")

        mock_v2.assert_called_once_with("key", "secret", url=None)

        assert client.http_client == mock_v2.return_value.http_client


def test_create_organization_with_structured_address(requests_mock):
    client = Client(key="EXOtest", secret="test")

    expected_response = {
        "id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
        "status": "active",
        "billing-address": {
            "name": "ACME Corporation",
            "street-name": "Route de Meyrin",
            "building-number": "10",
            "city": "Geneva",
            "postal-code": "1217",
            "country": "CH",
        },
    }

    requests_mock.post(
        "https://partner-api.exoscale.com/v1.alpha/distributor/organization",
        status_code=200,
        json=expected_response,
    )

    result = client.create_distributor_organization(
        display_name="ACME Corporation",
        billing_address={
            "name": "ACME Corporation",
            "street-name": "Route de Meyrin",
            "building-number": "10",
            "city": "Geneva",
            "postal-code": "1217",
            "country": "CH",
        },
        owner_email="owner@acme.com",
    )

    assert result["id"] == expected_response["id"]
    assert result["status"] == "active"
    assert result["billing-address"]["country"] == "CH"


def test_create_organization_with_optional_fields(requests_mock):
    client = Client(key="EXOtest", secret="test")

    expected_response = {
        "id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
        "status": "active",
        "billing-address": {
            "name": "Test GmbH",
            "street-name": "Hauptstraße",
            "building-number": "42",
            "city": "Berlin",
            "postal-code": "10115",
            "country": "DE",
            "address": "Additional address information",
        },
        "client-id": "custom-client-123",
    }

    requests_mock.post(
        "https://partner-api.exoscale.com/v1.alpha/distributor/organization",
        status_code=200,
        json=expected_response,
    )

    result = client.create_distributor_organization(
        display_name="Test GmbH",
        billing_address={
            "name": "Test GmbH",
            "street-name": "Hauptstraße",
            "building-number": "42",
            "city": "Berlin",
            "postal-code": "10115",
            "country": "DE",
            "address": "Additional address information",
        },
        owner_email="owner@test.de",
        client_id="custom-client-123",
    )

    assert result["id"] == expected_response["id"]
    assert result["client-id"] == "custom-client-123"
    assert (
        result["billing-address"]["address"]
        == "Additional address information"
    )


def test_create_organization_minimal_billing_address(requests_mock):
    client = Client(key="EXOtest", secret="test")

    expected_response = {
        "id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
        "status": "active",
        "billing-address": {
            "name": "Société Française",
            "street-name": "Rue de la Paix",
            "city": "Paris",
            "postal-code": "75001",
            "country": "FR",
        },
    }

    requests_mock.post(
        "https://partner-api.exoscale.com/v1.alpha/distributor/organization",
        status_code=200,
        json=expected_response,
    )

    # Test without optional building-number and address fields
    result = client.create_distributor_organization(
        display_name="Société Française",
        billing_address={
            "name": "Société Française",
            "street-name": "Rue de la Paix",
            "city": "Paris",
            "postal-code": "75001",
            "country": "FR",
        },
        owner_email="owner@societe.fr",
    )

    assert result["id"] == expected_response["id"]
    assert result["billing-address"]["country"] == "FR"
    assert "building-number" not in result["billing-address"]


def test_list_organizations(requests_mock):
    client = Client(key="EXOtest", secret="test")

    expected_response = {
        "organizations": [
            {
                "id": "org-1",
                "status": "active",
                "billing-address": {
                    "name": "Org 1",
                    "street-name": "Street 1",
                    "city": "City 1",
                    "postal-code": "1000",
                    "country": "CH",
                },
            },
            {
                "id": "org-2",
                "status": "suspended",
                "billing-address": {
                    "name": "Org 2",
                    "street-name": "Street 2",
                    "city": "City 2",
                    "postal-code": "2000",
                    "country": "DE",
                },
            },
        ]
    }

    requests_mock.get(
        "https://partner-api.exoscale.com/v1.alpha/distributor/organization",
        status_code=200,
        json=expected_response,
    )

    result = client.list_distributor_organizations()

    assert len(result["organizations"]) == 2
    assert result["organizations"][0]["id"] == "org-1"
    assert result["organizations"][1]["status"] == "suspended"
