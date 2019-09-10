#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale import *

_ALICE_API_KEY = "alice_api_key"
_ALICE_API_SECRET = "alice_api_secret"
_BOB_API_KEY = "bob_api_key"
_BOB_API_SECRET = "bob_api_secret"


class TestConfig:
    def test_params(self):
        exo = Exoscale(api_key=_ALICE_API_KEY, api_secret=_ALICE_API_SECRET)
        assert exo.api_key == _ALICE_API_KEY
        assert exo.api_secret == _ALICE_API_SECRET

    def test_envvars(self, monkeypatch):
        monkeypatch.setenv("EXOSCALE_API_KEY", _ALICE_API_KEY)
        monkeypatch.setenv("EXOSCALE_API_SECRET", _ALICE_API_SECRET)

        exo = Exoscale()
        assert exo.api_key == _ALICE_API_KEY
        assert exo.api_secret == _ALICE_API_SECRET

    def test_file_no_default_profile(self, tmp_path):
        f = tmp_path / "config.toml"

        f.write_text(
            """
[[profiles]]
name = "alice"
api_key = "{alice_api_key}"
api_secret = "{alice_api_secret}"

[[profiles]]
name = "bob"
api_key = "{bob_api_key}"
api_secret = "{bob_api_secret}"
""".format(
                alice_api_key=_ALICE_API_KEY,
                alice_api_secret=_ALICE_API_SECRET,
                bob_api_key=_BOB_API_KEY,
                bob_api_secret=_BOB_API_SECRET,
            )
        )

        exo = Exoscale(config_file=f)
        assert exo.api_key == _ALICE_API_KEY
        assert exo.api_secret == _ALICE_API_SECRET

    def test_file_default_profile(self, tmp_path):
        f = tmp_path / "config.toml"

        f.write_text(
            """
default_profile = "bob"

[[profiles]]
name = "alice"
api_key = "{alice_api_key}"
api_secret = "{alice_api_secret}"

[[profiles]]
name = "bob"
api_key = "{bob_api_key}"
api_secret = "{bob_api_secret}"
""".format(
                alice_api_key=_ALICE_API_KEY,
                alice_api_secret=_ALICE_API_SECRET,
                bob_api_key=_BOB_API_KEY,
                bob_api_secret=_BOB_API_SECRET,
            )
        )

        exo = Exoscale(config_file=f)
        assert exo.api_key == _BOB_API_KEY
        assert exo.api_secret == _BOB_API_SECRET

    def test_file_profile_param(self, tmp_path):
        f = tmp_path / "config.toml"

        f.write_text(
            """
[[profiles]]
name = "alice"
api_key = "{alice_api_key}"
api_secret = "{alice_api_secret}"

[[profiles]]
name = "bob"
api_key = "{bob_api_key}"
api_secret = "{bob_api_secret}"
""".format(
                alice_api_key=_ALICE_API_KEY,
                alice_api_secret=_ALICE_API_SECRET,
                bob_api_key=_BOB_API_KEY,
                bob_api_secret=_BOB_API_SECRET,
            )
        )

        exo = Exoscale(config_file=f, profile="bob")
        assert exo.api_key == _BOB_API_KEY
        assert exo.api_secret == _BOB_API_SECRET

        with pytest.raises(ConfigurationError) as excinfo:
            exo = Exoscale(config_file=f, profile="lolnope")
            assert exo is None
        assert excinfo.type == ConfigurationError
        assert 'profile "lolnope" not found' in str(excinfo.value)

    def test_file_errors(self, tmp_path):
        f = tmp_path / "config.toml"

        f.write_text("")
        with pytest.raises(ConfigurationError) as excinfo:
            exo = Exoscale(config_file=f)
            assert exo is None
        assert excinfo.type == ConfigurationError
        assert "no profiles configured" in str(excinfo.value)
