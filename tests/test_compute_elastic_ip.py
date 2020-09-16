#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.compute import *


class TestComputeElasticIP:
    def test_attach_instance(self, exo, eip, instance):
        elastic_ip = ElasticIP._from_cs(exo.compute, eip())
        instance = Instance._from_cs(exo.compute, instance())

        elastic_ip.attach_instance(instance)

        res = exo.compute.cs.listNics(virtualmachineid=instance.id, fetch_list=True)
        assert (
            instance._default_nic(res)["secondaryip"][0]["ipaddress"]
            == elastic_ip.address
        )

    def test_detach_instance(self, exo, eip, instance):
        elastic_ip = ElasticIP._from_cs(exo.compute, eip())
        instance = Instance._from_cs(exo.compute, instance())

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

    def test_set_reverse_dns(self, exo, eip, test_reverse_dns):
        elastic_ip = ElasticIP._from_cs(exo.compute, eip())

        elastic_ip.set_reverse_dns(record=test_reverse_dns)

        res = exo.compute.cs.queryReverseDnsForPublicIpAddress(id=elastic_ip.id)
        assert res["publicipaddress"]["reversedns"][0]["domainname"] == test_reverse_dns

    def test_unset_reverse_dns(self, exo, eip, test_reverse_dns):
        elastic_ip = ElasticIP._from_cs(exo.compute, eip())

        res = exo.compute.cs.updateReverseDnsForPublicIpAddress(
            id=elastic_ip.id, domainname=test_reverse_dns
        )
        assert res["publicipaddress"]["reversedns"][0]["domainname"] == test_reverse_dns

        elastic_ip.unset_reverse_dns()

        res = exo.compute.cs.queryReverseDnsForPublicIpAddress(id=elastic_ip.id)
        assert len(res["publicipaddress"]["reversedns"]) == 0

    def test_description_is_optional(self, exo, eip):
        response = eip()
        # The eip() fixture has a description set - del'ing it here is much cheaper
        # than writing a new fixture just for this particular case.
        del response["description"]
        elastic_ip = ElasticIP._from_cs(exo.compute, response)
        assert elastic_ip.description == ""

    def test_update(self, exo, eip, test_description):
        elastic_ip = ElasticIP._from_cs(exo.compute, eip())
        description_edited = test_description + " (edited)"
        healthcheck_mode = "https"
        healthcheck_port = 443
        healthcheck_path = "/test"
        healthcheck_interval = 5
        healthcheck_timeout = 3
        healthcheck_strikes_ok = 2
        healthcheck_strikes_fail = 1
        healthcheck_tls_sni = "example.net"
        healthcheck_tls_skip_verify = True

        elastic_ip.update(
            description=description_edited,
            healthcheck_mode=healthcheck_mode,
            healthcheck_path=healthcheck_path,
            healthcheck_port=healthcheck_port,
            healthcheck_interval=healthcheck_interval,
            healthcheck_timeout=healthcheck_timeout,
            healthcheck_strikes_ok=healthcheck_strikes_ok,
            healthcheck_strikes_fail=healthcheck_strikes_fail,
            healthcheck_tls_sni=healthcheck_tls_sni,
            healthcheck_tls_skip_verify=healthcheck_tls_skip_verify,
        )

        [res] = exo.compute.cs.listPublicIpAddresses(id=elastic_ip.id, fetch_list=True)
        assert res["description"] == description_edited
        assert elastic_ip.description == description_edited
        assert "healthcheck" in res.keys()
        assert res["healthcheck"]["mode"] == healthcheck_mode
        assert elastic_ip.healthcheck_mode == healthcheck_mode
        assert res["healthcheck"]["path"] == healthcheck_path
        assert elastic_ip.healthcheck_path == healthcheck_path
        assert res["healthcheck"]["port"] == healthcheck_port
        assert elastic_ip.healthcheck_port == healthcheck_port
        assert res["healthcheck"]["interval"] == healthcheck_interval
        assert elastic_ip.healthcheck_interval == healthcheck_interval
        assert res["healthcheck"]["timeout"] == healthcheck_timeout
        assert elastic_ip.healthcheck_timeout == healthcheck_timeout
        assert res["healthcheck"]["strikes-ok"] == healthcheck_strikes_ok
        assert elastic_ip.healthcheck_strikes_ok == healthcheck_strikes_ok
        assert res["healthcheck"]["strikes-fail"] == healthcheck_strikes_fail
        assert elastic_ip.healthcheck_strikes_fail == healthcheck_strikes_fail
        assert res["healthcheck"]["tls-sni"] == healthcheck_tls_sni
        assert elastic_ip.healthcheck_tls_sni == healthcheck_tls_sni
        assert res["healthcheck"]["tls-skip-verify"] == healthcheck_tls_skip_verify
        assert elastic_ip.healthcheck_tls_skip_verify == healthcheck_tls_skip_verify

    def test_delete(self, exo, eip, instance):
        elastic_ip = ElasticIP._from_cs(exo.compute, eip(teardown=False))
        elastic_ip_id = elastic_ip.id
        instance = Instance._from_cs(exo.compute, instance())

        res = exo.compute.cs.listNics(virtualmachineid=instance.id, fetch_list=True)
        exo.compute.cs.addIpToNic(
            nicid=instance._default_nic(res)["id"], ipaddress=elastic_ip.address
        )

        elastic_ip.delete(detach_instances=True)
        assert elastic_ip.id is None

        res = exo.compute.cs.listPublicIpAddresses(id=elastic_ip_id, fetch_list=True)
        assert len(res) == 0

    def test_properties(self, exo, eip, instance, test_reverse_dns):
        elastic_ip = ElasticIP._from_cs(exo.compute, eip())
        instance = Instance._from_cs(exo.compute, instance())

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
