import pytest
from exoscale.api.v2 import Client
from exoscale.api.exceptions import (
    ExoscaleAPIClientException,
    ExoscaleAPIServerException,
    ExoscaleAPIAuthException,
)


def test_client_creation():
    c = Client("key", "secret", zone="at-vie-1")
    assert hasattr(c, "list_zones")

    # incorrect zone
    with pytest.raises(TypeError) as exc:
        Client("key", "secret", zone="us-east-1")
    assert "Invalid zone" in str(exc.value)

    # unhandled kwarg
    with pytest.raises(TypeError) as exc:
        Client("key", "secret", region="ch-dk-2")
    assert "Unhandled keyword argument" in str(exc.value)

    # create with custom URL
    c = Client("key", "secret", url="http://localhost:8000/v2")
    assert hasattr(c, "list_zones")


def test_client_error_handling(requests_mock):
    client = Client(key="EXOtest", secret="sdsd")

    # Mock a 403 authentication error
    requests_mock.get(
        "https://api-ch-gva-2.exoscale.com/v2/instance/85664334-0fd5-47bd-94a1-b4f40b1d2eb7",
        status_code=403,
        text='{"message":"Invalid request signature"}',
    )
    try:
        client_with_wrong_key = Client(key="EXOtest", secret="wrong_secret")
        client_with_wrong_key.get_instance(
            id="85664334-0fd5-47bd-94a1-b4f40b1d2eb7"
        )
    except ExoscaleAPIAuthException as e:
        assert "Authentication error 403" in str(e)
        assert '{"message":"Invalid request signature"}' in str(e)

    # Mock a 404 client error
    requests_mock.get(
        "https://api-ch-gva-2.exoscale.com/v2/instance/85664334-0fd5-47bd-94a1-b4f40b1d2eb7",
        status_code=404,
        text='{"message":"Instance not found"}',
    )
    try:
        client.get_instance(id="85664334-0fd5-47bd-94a1-b4f40b1d2eb7")
    except ExoscaleAPIClientException as e:
        assert "Client error 404" in str(e)
        assert '{"message":"Instance not found"}' in str(e)

    # Mock a 500 server error
    requests_mock.get(
        "https://api-ch-gva-2.exoscale.com/v2/500_error",
        status_code=500,
        text="Internal Server Error",
    )
    try:
        response = client.session.get(
            "https://api-ch-gva-2.exoscale.com/v2/500_error"
        )
        response.raise_for_status()
    except ExoscaleAPIServerException as e:
        assert "Server error 500" in str(e)
    except Exception as e:
        assert "500 Server Error" in str(e)


if __name__ == "__main__":
    pytest.main()
