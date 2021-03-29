#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pytest
import random
import string
import time
from boto3 import s3
from botocore.stub import Stubber
from datetime import datetime
from urllib.parse import urljoin
from uuid import uuid4

_DEFAULT_ZONE_NAME = "ch-gva-2"


def _random_str(length=10, charset=string.ascii_lowercase + string.digits):
    return "".join(random.choice(charset) for i in range(length))


def _random_uuid():
    return str(uuid4())


def _random_ip_address(v=4):
    from ipaddress import IPv4Address, IPv6Address

    if v == 4:
        return str(IPv4Address(random.randint(0, 2 ^ 32)))
    else:
        return str(IPv6Address(random.randint(0, 2 ^ 128 - 1)))


@pytest.fixture(autouse=True, scope="function")
def exo():
    import exoscale
    import requests_mock

    class ExoscaleMock(exoscale.Exoscale):
        def __init__(self, exo):
            self.exo = exo

            self.mocker = requests_mock.Mocker()
            self.mocker.start()

            self.boto_stub = Stubber(exo.storage.boto)
            self.boto_stub.activate()

        @property
        def compute(self):
            return self.exo.compute

        @property
        def iam(self):
            return self.exo.iam

        @property
        def dns(self):
            return self.exo.dns

        @property
        def storage(self):
            return self.exo.storage

        def mock_post(self, zone, url, resp):
            self.mocker.post(
                urljoin("https://api-{}.exoscale.com/v2.alpha/".format(zone), url),
                json=resp,
            )

        def mock_put(self, zone, url, resp):
            self.mocker.put(
                urljoin("https://api-{}.exoscale.com/v2.alpha/".format(zone), url),
                json=resp,
            )

        def mock_delete(self, zone, url, resp):
            self.mocker.delete(
                urljoin("https://api-{}.exoscale.com/v2.alpha/".format(zone), url),
                json=resp,
            )

        # FIXME: this method shall be renamed into mock_get() once we've finished
        # transitioning to the Public API V2.
        def mock_get_v2(self, zone, url, resp):
            self.mocker.get(
                urljoin("https://api-{}.exoscale.com/v2.alpha/".format(zone), url),
                json=resp,
            )

        def mock_get(self, url, resp, **kwargs):
            self.mocker.get(
                urljoin(self.exo.compute.endpoint, url),
                json=resp,
                headers={"Content-Type": "application/json"},
                **kwargs
            )

        def mock_list(self, list_command, results=[]):
            resources = {
                "listAffinityGroups": {
                    "res_key": "listaffinitygroupsresponse",
                    "res_type": "affinitygroup",
                },
                "listApiKeys": {
                    "res_key": "listapikeysreponse",
                    "res_type": "apikey",
                },
                "listDnsDomainRecords": {
                    "res_key": "listdnsdomainrecordsreponse",
                    "res_type": "records",
                },
                "listDnsDomains": {
                    "res_key": "listdnsdomainsreponse",
                    "res_type": "dnsdomain",
                },
                "listInstancePools": {
                    "res_key": "listinstancepoolsresponse",
                    "res_type": "instancepool",
                },
                "listNetworks": {
                    "res_key": "listnetworksresponse",
                    "res_type": "network",
                },
                "listNics": {
                    "res_key": "listnicsresponse",
                    "res_type": "nic",
                },
                "listPublicIpAddresses": {
                    "res_key": "listpublicipaddressesresponse",
                    "res_type": "ipaddress",
                },
                "listSecurityGroups": {
                    "res_key": "listsecuritygroupsresponse",
                    "res_type": "securitygroups",
                },
                "listServiceOfferings": {
                    "res_key": "listserviceofferingsresponse",
                    "res_type": "serviceoffering",
                },
                "listSnapshots": {
                    "res_key": "listsnapshotsresponse",
                    "res_type": "snapshot",
                },
                "listSSHKeyPairs": {
                    "res_key": "listsshkeypairsresponse",
                    "res_type": "sshkeypair",
                },
                "listTemplates": {
                    "res_key": "listtemplatesresponse",
                    "res_type": "template",
                },
                "listVirtualMachines": {
                    "res_key": "listvirtualmachinesreponse",
                    "res_type": "virtualmachine",
                },
                "listVolumes": {
                    "res_key": "listvolumesresponse",
                    "res_type": "volume",
                },
                "listZones": {
                    "res_key": "listzonesresponse",
                    "res_type": "zone",
                },
            }

            if list_command not in resources:
                raise Exception("{} command not supported".format(list_command))

            self.mock_get(
                "?command={}".format(list_command),
                {
                    resources[list_command]["res_key"]: {
                        "count": len(results),
                        resources[list_command]["res_type"]: results,
                    }
                },
            )

        def mock_query_async_job_result(self, result=None):
            self.mock_get(
                "?command=queryAsyncJobResult",
                {
                    "queryasyncjobresultresponse": {
                        "jobresult": result if result else {"success": True},
                        "jobresultcode": 0,
                        "jobstatus": 1,
                    }
                },
            )

        def mock_get_operation(self, zone, op_id, ref_id, result=None):
            self.mocker.get(
                "https://api-{}.exoscale.com/v2.alpha/operation/{}".format(zone, op_id),
                json=result
                if result
                else {
                    "id": op_id,
                    "state": "success",
                    "reference": {"id": ref_id},
                },
            )

    return ExoscaleMock(exoscale.Exoscale(api_key="test", api_secret="test"))


@pytest.fixture(autouse=True, scope="function")
def zone():
    def _zone(name=_DEFAULT_ZONE_NAME, **kwargs):
        return {**{"id": _random_uuid(), "name": name}, **kwargs}

    yield _zone


@pytest.fixture(autouse=True, scope="function")
def instance_type():
    def _instance_type(**kwargs):
        return {
            **{
                "id": _random_uuid(),
                "name": "Medium",
                "cpunumber": 2,
                "memory": 4096,
                "zoneid": kwargs.get("zone_id", _random_uuid()),
            },
            **kwargs,
        }

    yield _instance_type


@pytest.fixture(autouse=True, scope="function")
def instance_template():
    def _instance_template(**kwargs):
        return {
            **{
                "id": _random_uuid(),
                "name": _random_str(),
                "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0000"),
                "size": 10737418240,
                "checksum": _random_str(length=32),
                "sshkeyenabled": True,
                "passwordenabled": True,
                "bootmode": "legacy",
                "zoneid": kwargs.get("zone_id", _random_uuid()),
            },
            **kwargs,
        }

    yield _instance_template


@pytest.fixture(autouse=True, scope="function")
def volume_snapshot():
    def _volume_snapshot(**kwargs):
        return {
            **{
                "id": _random_uuid(),
                "name": _random_str(),
                "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0000"),
                "volumeid": kwargs.get("volume_id", _random_uuid()),
                "size": 10737418240,
                "revertable": True,
                "state": "exported",
            },
            **kwargs,
        }

    yield _volume_snapshot


@pytest.fixture(autouse=True, scope="function")
def aag():
    def _anti_affinity_group(**kwargs):
        return {
            **{
                "id": _random_uuid(),
                "name": _random_str(),
                "type": "host anti-affinity",
            },
            **kwargs,
        }

    yield _anti_affinity_group


@pytest.fixture(autouse=True, scope="function")
def eip():
    def _elastic_ip(**kwargs):
        return {
            **{
                "id": _random_uuid(),
                "ipaddress": _random_ip_address(),
                "iselastic": True,
                "zoneid": kwargs.get("zone_id", _random_uuid()),
                "reversedns": [{"domainname": kwargs["reverse_dns"]}]
                if "reverse_dns" in kwargs
                else [],
            },
            **kwargs,
        }

    yield _elastic_ip


@pytest.fixture(autouse=True, scope="function")
def instance():
    def _instance(**kwargs):
        return {
            **{
                "id": _random_uuid(),
                "name": _random_str(),
                "displayname": kwargs.get("name", _random_str()),
                "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0000"),
                "zoneid": kwargs.get("zone_id", _random_uuid()),
                "templateid": kwargs.get("template_id", _random_uuid()),
                "serviceofferingid": kwargs.get("type_id", _random_uuid()),
                "securitygroup": [
                    {"id": id} for id in kwargs.get("security_group_ids", [])
                ],
                "affinitygroup": [
                    {"id": id} for id in kwargs.get("anti_affinity_group_ids", [])
                ],
                "nic": [
                    {
                        "id": _random_uuid(),
                        "isdefault": True,
                        "ipaddress": _random_ip_address(),
                        "ip6address": _random_ip_address(6),
                        "networkid": _random_uuid(),
                        "reversedns": [{"domainname": kwargs["reverse_dns"]}]
                        if "reverse_dns" in kwargs
                        else [],
                    }
                ]
                + [
                    {"id": _random_uuid(), "isdefault": False, "networkid": id}
                    for id in kwargs.get("private_network_ids", [])
                ],
                "state": "Running",
            },
            **kwargs,
        }

    yield _instance


@pytest.fixture(autouse=True, scope="function")
def instance_pool(instance):
    def _instance_pool(**kwargs):
        id = _random_uuid()
        zone_id = _random_uuid()
        type_id = _random_uuid()
        template_id = _random_uuid()
        rootdisksize = 10
        security_group_ids = [{"id": id} for id in kwargs.get("security_group_ids", [])]
        affinity_group_ids = [
            {"id": id} for id in kwargs.get("anti_affinity_group_ids", [])
        ]
        network_ids = [{"id": id} for id in kwargs.get("private_network_ids", [])]

        return {
            **{
                "id": kwargs.get("id", id),
                "name": _random_str(),
                "size": 1,
                "created": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0000"),
                "zoneid": kwargs.get("zone_id", zone_id),
                "templateid": kwargs.get("template_id", template_id),
                "serviceofferingid": kwargs.get("type_id", type_id),
                "rootdisksize": kwargs.get("rootdisksize", rootdisksize),
                "securitygroupids": security_group_ids,
                "affinitygroupids": affinity_group_ids,
                "networkids": network_ids,
                "state": "running",
                "virtualmachines": [
                    instance(
                        zone_id=kwargs.get("zone_id", zone_id),
                        type_id=kwargs.get("type_id", type_id),
                        template_id=kwargs.get("template_id", template_id),
                        rootdisksize=kwargs.get("rootdisksize", rootdisksize),
                        security_group_ids=security_group_ids,
                        anti_affinity_group_ids=affinity_group_ids,
                        private_network_ids=network_ids,
                        manager="instancepool",
                        managerid=kwargs.get("id", id),
                    )
                    for i in range(kwargs.get("size", 1))
                ],
            },
            **kwargs,
        }

    yield _instance_pool


@pytest.fixture(autouse=True, scope="function")
def nlb():
    def _nlb(**kwargs):
        return {
            **{
                "id": _random_uuid(),
                "name": _random_str(),
                "created-at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "ip": _random_ip_address(),
                "services": [],
                "state": "running",
            },
            **kwargs,
        }

    yield _nlb


@pytest.fixture(autouse=True, scope="function")
def nlb_service():
    def _nlb_service(**kwargs):
        return {
            **{
                "id": _random_uuid(),
                "name": _random_str(),
                "instance-pool": {"id": _random_uuid()},
                "protocol": "tcp",
                "port": 80,
                "target-port": 8080,
                "strategy": "round-robin",
                "healthcheck": {
                    "mode": "tcp",
                    "port": 8080,
                    "interval": 10,
                    "timeout": 5,
                    "retries": 1,
                },
                "healthcheck-status": [
                    {"public-ip": _random_ip_address(), "status": "success"}
                ],
                "state": "running",
            },
            **kwargs,
        }

    yield _nlb_service


@pytest.fixture(autouse=True, scope="function")
def privnet():
    def _private_network(**kwargs):
        return {
            **{
                "id": _random_uuid(),
                "name": _random_str(),
                "displaytext": kwargs.get("description", ""),
                "zoneid": _random_uuid(),
            },
            **kwargs,
        }

    yield _private_network


@pytest.fixture(autouse=True, scope="function")
def sg():
    def _security_group(**kwargs):
        return {
            **{
                "id": _random_uuid(),
                "name": _random_str(),
                "ingressrule": kwargs.get("ingress", []),
                "egressrule": kwargs.get("egress", []),
            },
            **kwargs,
        }

    yield _security_group


@pytest.fixture(autouse=True, scope="function")
def sshkey():
    def _ssh_key(**kwargs):
        return {
            **{
                "name": _random_str(),
                "fingerprint": ":".join(
                    ["{:02x}".format(random.randint(0, 255)) for i in range(16)]
                ),
                "privatekey": "-----BEGIN RSA PRIVATE KEY-----\n"
                + "\n".join(
                    [
                        _random_str(
                            64,
                            charset=string.ascii_lowercase
                            + string.ascii_uppercase
                            + string.digits
                            + "/+",
                        )
                        for i in range(10)
                    ]
                )
                + "-----END RSA PRIVATE KEY-----\n",
            },
            **kwargs,
        }

    yield _ssh_key


@pytest.fixture(autouse=True, scope="function")
def apikey():
    def _api_key(**kwargs):
        return {
            **{
                "name": _random_str(),
                "key": _random_str(),
                "type": "restricted" if "operations" in kwargs else "unrestricted",
            },
            **kwargs,
        }

    yield _api_key


@pytest.fixture(autouse=True, scope="function")
def domain():
    def _domain(**kwargs):
        name = _random_str() + ".com"
        created = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0000")

        return {
            **{
                "autorenew": False,
                "created": created,
                "id": random.randint(1, 65535),
                "name": name,
                "private_whois": False,
                "state": "hosted",
                "unicodename": name,
                "updated": created,
            },
            **kwargs,
        }

    yield _domain


@pytest.fixture(autouse=True, scope="function")
def domain_record():
    def _domain_record(**kwargs):
        created = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0000")

        return {
            **{
                "created_at": created,
                "id": random.randint(1, 65535),
                "domain_id": random.randint(1, 65535),
                "name": _random_str(),
                "record_type": "A",
                "content": _random_ip_address(),
                "ttl": 3600,
                "updated_at": created,
            },
            **kwargs,
        }

    yield _domain_record
