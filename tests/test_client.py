import pytest
from exoscale.api.v2 import Client, _poll_interval
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

    # Mock a 503 server error
    requests_mock.get(
        "https://api-ch-gva-2.exoscale.com/v2/template",
        status_code=503,
        text='{"message":"Endpoint template temporarily unavailable"}',
    )
    try:
        client.list_templates()
    except ExoscaleAPIServerException as e:
        assert "Server error 503" in str(e)
        assert (
            '{"message":"Endpoint template temporarily unavailable"}' in str(e)
        )


def test_wait_interval():
    assert _poll_interval(25) == 3
    assert 3 < _poll_interval(33) < 4
    assert 8 < _poll_interval(120) < 9
    assert 40 < _poll_interval(600) < 41
    assert _poll_interval(1000) == 60
    assert _poll_interval(999999) == 60


def test_operation_poll_failure(requests_mock):
    requests_mock.get(
        "https://api-ch-gva-2.exoscale.com/v2/operation/e2047130-b86e-11ef-83b3-0d8312b2c2d7",  # noqa
        status_code=200,
        text='{"id": "4c5547c0-b870-11ef-83b3-0d8312b2c2d7", "state": "failure", "reason": "unknown", "reference": {"id": "97d7426f-8b25-4591-91d5-4a19e9a1d61a", "link": "/v2/sks-cluster/97d7426f-8b25-4591-91d5-4a19e9a1d61a", "command": "get-sks-cluster"}}',  # noqa
    )

    client = Client(key="EXOtest", secret="sdsd")
    try:
        client.wait(operation_id="e2047130-b86e-11ef-83b3-0d8312b2c2d7")
    except ExoscaleAPIServerException as e:
        assert "Operation error: failure" in str(e)
    else:
        assert False, "exception not raised"


def test_operation_abort_on_500(requests_mock):
    requests_mock.get(
        "https://api-ch-gva-2.exoscale.com/v2/operation/e2047130-b86e-11ef-83b3-0d8312b2c2d7",  # noqa
        status_code=500,
        text='{"message": "server error"}',
    )

    client = Client(key="EXOtest", secret="sdsd")
    try:
        client.wait(operation_id="e2047130-b86e-11ef-83b3-0d8312b2c2d7")
    except ExoscaleAPIServerException as e:
        assert "Server error while polling operation" in str(e)
    else:
        assert False, "exception not raised"


def test_operation_invalid_state(requests_mock):
    requests_mock.get(
        "https://api-ch-gva-2.exoscale.com/v2/operation/e2047130-b86e-11ef-83b3-0d8312b2c2d7",  # noqa
        status_code=200,
        text='{"id": "4c5547c0-b870-11ef-83b3-0d8312b2c2d7", "state": "weird", "reference": {"id": "97d7426f-8b25-4591-91d5-4a19e9a1d61a", "link": "/v2/sks-cluster/97d7426f-8b25-4591-91d5-4a19e9a1d61a", "command": "get-sks-cluster"}}',  # noqa
    )

    client = Client(key="EXOtest", secret="sdsd")
    try:
        client.wait(operation_id="e2047130-b86e-11ef-83b3-0d8312b2c2d7")
    except ExoscaleAPIServerException as e:
        assert "Invalid operation state: weird" in str(e)
    else:
        assert False, "exception not raised"


if __name__ == "__main__":
    pytest.main()
