#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.compute import *


class TestComputeSSHKey:
    def test_delete(self, exo, sshkey):
        ssh_key = SSHKey.from_cs(exo.compute, sshkey(teardown=False))
        ssh_key_name = ssh_key.name

        ssh_key.delete()
        assert ssh_key.name is None

        res = exo.compute.cs.listSSHKeyPairs(name=ssh_key_name, fetch_list=True)
        assert len(res) == 0
