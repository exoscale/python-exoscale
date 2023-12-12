import pytest

from exoscale.api.v2 import Client


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
