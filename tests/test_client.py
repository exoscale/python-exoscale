import json

from unittest.mock import patch

from exoscale.api.exceptions import (
    ExoscaleAPIAuthException,
    ExoscaleAPIClientException,
    ExoscaleAPIServerException,
)
from exoscale.api.v2 import Client, _poll_interval

import pytest


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
        raise AssertionError("exception not raised")


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
        raise AssertionError("exception not raised")


def _mock_poll_response(poll_counts, status_code=200, result="success"):
    return [
        {
            "status_code": status_code,
            "text": '{"id": "4c5547c0-b870-11ef-83b3-0d8312b2c2d7", "state": "pending", "reference": {"id": "97d7426f-8b25-4591-91d5-4a19e9a1d61a", "link": "/v2/sks-cluster/97d7426f-8b25-4591-91d5-4a19e9a1d61a", "command": "get-sks-cluster"}}',  # noqa
        }
    ] * (poll_counts - 1) + [
        {
            "status_code": status_code,
            "text": json.dumps(
                {
                    "id": "4c5547c0-b870-11ef-83b3-0d8312b2c2d7",
                    "state": result,
                    "reason": "some reason",
                    "reference": {
                        "id": "97d7426f-8b25-4591-91d5-4a19e9a1d61a",
                        "link": "/v2/sks-cluster/97d7426f-8b25-4591-91d5-4a19e9a1d61a",  # noqa
                        "command": "get-sks-cluster",
                    },
                }
            ),
        }
    ]


def test_wait_time_success(requests_mock):
    requests_mock.get(
        "https://api-ch-gva-2.exoscale.com/v2/operation/e2047130-b86e-11ef-83b3-0d8312b2c2d7",  # noqa
        _mock_poll_response(3),
    )
    with patch(
        "exoscale.api.v2._time",
        side_effect=[
            0,  # start of poll
            1,  # duration of first loop: 1s
            5,  # duration of second loop: 4s
        ],
    ) as time, patch("exoscale.api.v2._sleep") as sleep:
        client = Client(key="EXOtest", secret="sdsd")
        client.wait(operation_id="e2047130-b86e-11ef-83b3-0d8312b2c2d7")
        assert len(time.call_args_list) == 3
        assert len(sleep.call_args_list) == 2


def test_wait_time_poll_errors(requests_mock):
    requests_mock.get(
        "https://api-ch-gva-2.exoscale.com/v2/operation/e2047130-b86e-11ef-83b3-0d8312b2c2d7",  # noqa
        _mock_poll_response(6, status_code=500),
    )
    with patch(
        "exoscale.api.v2._time",
        side_effect=[
            0,  # start of poll
        ],
    ) as time, patch("exoscale.api.v2._sleep") as sleep:
        client = Client(key="EXOtest", secret="sdsd")
        try:
            client.wait(operation_id="e2047130-b86e-11ef-83b3-0d8312b2c2d7")
        except ExoscaleAPIServerException:
            pass
        else:
            raise AssertionError("Exception not raised")
        assert len(time.call_args_list) == 1
        assert len(sleep.call_args_list) == 4


def test_wait_time_failure(requests_mock):
    requests_mock.get(
        "https://api-ch-gva-2.exoscale.com/v2/operation/e2047130-b86e-11ef-83b3-0d8312b2c2d7",  # noqa
        _mock_poll_response(3, result="failure"),
    )
    with patch(
        "exoscale.api.v2._time",
        side_effect=[
            0,  # start of poll
            1,  # duration of first loop: 1s
            5,  # duration of second loop: 4s
        ],
    ) as time, patch("exoscale.api.v2._sleep") as sleep:
        client = Client(key="EXOtest", secret="sdsd")
        try:
            client.wait(operation_id="e2047130-b86e-11ef-83b3-0d8312b2c2d7")
        except ExoscaleAPIServerException as e:
            assert "Operation error" in str(e)
        else:
            raise AssertionError("Exception not raised")
        assert len(time.call_args_list) == 3
        assert len(sleep.call_args_list) == 2


if __name__ == "__main__":
    pytest.main()
