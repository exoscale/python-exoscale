from exoscale.api.v2 import Client


def test_client_creation():
    c = Client("key", "secret", zone="at-vie-1")
    assert hasattr(c, "list_zones")
