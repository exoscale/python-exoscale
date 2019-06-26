#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.compute import *


class TestComputeElasticIP:
    def test_attach_instance(self, exo, eip, instance):
        elastic_ip = ElasticIP.from_cs(exo.compute, eip())
        instance = Instance.from_cs(exo.compute, instance())

        elastic_ip.attach_instance(instance)

        res = exo.compute.cs.listNics(virtualmachineid=instance.id, fetch_list=True)
        assert (
            instance._default_nic(res)["secondaryip"][0]["ipaddress"]
            == elastic_ip.address
        )

    def test_detach_instance(self, exo, eip, instance):
        elastic_ip = ElasticIP.from_cs(exo.compute, eip())
        instance = Instance.from_cs(exo.compute, instance())

        res = exo.compute.cs.listNics(virtualmachineid=instance.id, fetch_list=True)
        exo.compute.cs.addIpToNic(
            nicid=instance._default_nic(res)["id"], ipaddress=elastic_ip.address
        )

        res = exo.compute.cs.listNics(virtualmachineid=instance.id, fetch_list=True)
        assert (
            instance._default_nic(res)["secondaryip"][0]["ipaddress"]
            == elastic_ip.address
        )

        elastic_ip.detach_instance(instance)

        res = exo.compute.cs.listNics(virtualmachineid=instance.id, fetch_list=True)
        assert "secondaryip" not in instance._default_nic(res)

    def test_update_healthcheck(self, exo, eip):
        elastic_ip = ElasticIP.from_cs(exo.compute, eip())
        healthcheck_mode = "http"
        healthcheck_port = 80
        healthcheck_path = "/test"
        healthcheck_interval = 5
        healthcheck_timeout = 3
        healthcheck_strikes_ok = 2
        healthcheck_strikes_fail = 1

        elastic_ip.update(
            healthcheck_mode=healthcheck_mode,
            healthcheck_path=healthcheck_path,
            healthcheck_port=healthcheck_port,
            healthcheck_interval=healthcheck_interval,
            healthcheck_timeout=healthcheck_timeout,
            healthcheck_strikes_ok=healthcheck_strikes_ok,
            healthcheck_strikes_fail=healthcheck_strikes_fail,
        )

        [res] = exo.compute.cs.listPublicIpAddresses(id=elastic_ip.id, fetch_list=True)
        assert "healthcheck" in res.keys()
        assert res["healthcheck"]["mode"] == healthcheck_mode
        assert res["healthcheck"]["path"] == healthcheck_path
        assert res["healthcheck"]["port"] == healthcheck_port
        assert res["healthcheck"]["interval"] == healthcheck_interval
        assert res["healthcheck"]["timeout"] == healthcheck_timeout
        assert res["healthcheck"]["strikes-ok"] == healthcheck_strikes_ok
        assert res["healthcheck"]["strikes-fail"] == healthcheck_strikes_fail
        assert elastic_ip.healthcheck_mode == healthcheck_mode
        assert elastic_ip.healthcheck_path == healthcheck_path
        assert elastic_ip.healthcheck_port == healthcheck_port
        assert elastic_ip.healthcheck_interval == healthcheck_interval
        assert elastic_ip.healthcheck_timeout == healthcheck_timeout
        assert elastic_ip.healthcheck_strikes_ok == healthcheck_strikes_ok
        assert elastic_ip.healthcheck_strikes_fail == healthcheck_strikes_fail

    def test_set_reverse_dns(self, exo, eip, test_reverse_dns):
        elastic_ip = ElasticIP.from_cs(exo.compute, eip())

        elastic_ip.set_reverse_dns(record=test_reverse_dns)

        res = exo.compute.cs.queryReverseDnsForPublicIpAddress(id=elastic_ip.id)
        assert res["publicipaddress"]["reversedns"][0]["domainname"] == test_reverse_dns

    def test_unset_reverse_dns(self, exo, eip, test_reverse_dns):
        elastic_ip = ElasticIP.from_cs(exo.compute, eip())

        res = exo.compute.cs.updateReverseDnsForPublicIpAddress(
            id=elastic_ip.id, domainname=test_reverse_dns
        )
        assert res["publicipaddress"]["reversedns"][0]["domainname"] == test_reverse_dns

        elastic_ip.unset_reverse_dns()

        res = exo.compute.cs.queryReverseDnsForPublicIpAddress(id=elastic_ip.id)
        assert len(res["publicipaddress"]["reversedns"]) == 0

    def test_delete(self, exo, eip, instance):
        elastic_ip = ElasticIP.from_cs(exo.compute, eip(teardown=False))
        elastic_ip_id = elastic_ip.id
        instance = Instance.from_cs(exo.compute, instance())

        res = exo.compute.cs.listNics(virtualmachineid=instance.id, fetch_list=True)
        exo.compute.cs.addIpToNic(
            nicid=instance._default_nic(res)["id"], ipaddress=elastic_ip.address
        )

        elastic_ip.delete(detach_instances=True)
        assert elastic_ip.id is None

        res = exo.compute.cs.listPublicIpAddresses(id=elastic_ip_id, fetch_list=True)
        assert len(res) == 0

    def test_properties(self, exo, eip, instance, test_reverse_dns):
        elastic_ip = ElasticIP.from_cs(exo.compute, eip())
        instance = Instance.from_cs(exo.compute, instance())

        instance_nics = exo.compute.cs.listNics(
            virtualmachineid=instance.id, fetch_list=True
        )
        default_nic = instance._default_nic(instance_nics)
        exo.compute.cs.addIpToNic(nicid=default_nic["id"], ipaddress=elastic_ip.address)

        elastic_ip_instances = list(elastic_ip.instances)
        assert len(elastic_ip_instances) == 1
        assert elastic_ip_instances[0].name == instance.name

        exo.compute.cs.updateReverseDnsForPublicIpAddress(
            id=elastic_ip.id, domainname=test_reverse_dns
        )
        assert elastic_ip.reverse_dns == test_reverse_dns
