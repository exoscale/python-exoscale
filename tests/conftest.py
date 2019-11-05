#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pytest
import random
import string
import time
from datetime import datetime

_DEFAULT_ZONE_NAME = "ch-gva-2"
_DEFAULT_ZONE_ID = "1128bd56-b4d9-4ac6-a7b9-c715b187ce11"


def _random_str():
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for i in range(10))


@pytest.fixture(autouse=True, scope="module")
def test_prefix():
    return "test-python-exoscale"


@pytest.fixture(autouse=True, scope="module")
def test_description():
    return "Created by the python-exoscale library"


@pytest.fixture(autouse=True, scope="module")
def test_instance_service_offering_id():
    # Micro
    return "71004023-bb72-4a97-b1e9-bc66dfce9470"


@pytest.fixture(autouse=True, scope="module")
def test_instance_template_name():
    return "Linux Ubuntu 18.04 LTS 64-bit"


@pytest.fixture(autouse=True, scope="module")
def test_instance_template_id():
    # Linux Ubuntu 18.04 LTS 64-bit @ ch-gva-2
    return "45346aba-6027-45bc-ad1e-bd1f563c2d84"


@pytest.fixture(autouse=True, scope="module")
def test_reverse_dns():
    return "python.exoscale.com."


@pytest.fixture(autouse=True, scope="function")
def timing():
    print(
        "\n>>> {}: test started at {}".format(
            os.environ.get("PYTEST_CURRENT_TEST"), datetime.now()
        )
    )
    started = time.time()

    yield

    print(
        "\n<<< {}: test stopped at {}".format(
            os.environ.get("PYTEST_CURRENT_TEST"), datetime.now()
        )
    )

    print("--- Test duration: {:0.2f}s\n".format(time.time() - started))


@pytest.fixture(autouse=True, scope="class")
def exo():
    import exoscale

    return exoscale.Exoscale()


@pytest.fixture(autouse=True, scope="class")
def zone(exo):
    def _zone(name):
        return exo.compute.cs.listZones(name=name, fetch_list=True)[0]

    return _zone


@pytest.fixture(autouse=True, scope="class")
def instance_type(exo):
    def _instance_type(id=None, name=None):
        return exo.compute.cs.listServiceOfferings(id=id, name=name, fetch_list=True)[0]

    return _instance_type


@pytest.fixture(autouse=True, scope="class")
def instance_template(exo):
    def _instance_template(id=None, name=None, zone_id=None):
        return exo.compute.cs.listTemplates(
            id=id, name=name, zoneid=zone_id, fetch_list=True
        )[0]

    return _instance_template


@pytest.fixture(autouse=True, scope="function")
def aag(exo, test_prefix, test_description):
    anti_affinity_groups = []

    def _anti_affinity_group(name=None, description=test_description, teardown=True):
        anti_affinity_group = exo.compute.cs.createAffinityGroup(
            name=name if name else "-".join([test_prefix, _random_str()]),
            description=description,
            type="host anti-affinity",
        )["affinitygroup"]

        if teardown:
            anti_affinity_groups.append(anti_affinity_group)

        return anti_affinity_group

    yield _anti_affinity_group

    for anti_affinity_group in anti_affinity_groups:
        res = exo.compute.cs.deleteAffinityGroup(id=anti_affinity_group["id"])
        assert res["success"]


@pytest.fixture(autouse=True, scope="function")
def eip(exo, zone, test_description):
    elastic_ips = []

    def _elastic_ip(
        zone_id=_DEFAULT_ZONE_ID, description=test_description, teardown=True
    ):
        elastic_ip = exo.compute.cs.associateIpAddress(
            zoneid=zone_id, description=description
        )["ipaddress"]

        if teardown:
            elastic_ips.append(elastic_ip)

        return elastic_ip

    yield _elastic_ip

    for elastic_ip in elastic_ips:
        res = exo.compute.cs.disassociateIpAddress(id=elastic_ip["id"])
        assert res["success"]


@pytest.fixture(autouse=True, scope="function")
def instance(
    exo,
    instance_type,
    instance_template,
    test_prefix,
    test_instance_service_offering_id,
    test_instance_template_id,
):
    instances = []

    def _instance(
        name=None,
        type_id=test_instance_service_offering_id,
        template_id=test_instance_template_id,
        zone_id=_DEFAULT_ZONE_ID,
        volume_size=10,
        security_groups=None,
        anti_affinity_groups=None,
        private_networks=None,
        start=True,
        teardown=True,
    ):
        instance = exo.compute.cs.deployVirtualMachine(
            name=name if name else "-".join([test_prefix, _random_str()]),
            displayname=name,
            zoneid=zone_id,
            templateid=template_id,
            serviceofferingid=type_id,
            root_disk_size=volume_size,
            securitygroupids=security_groups,
            affinitygroupids=anti_affinity_groups,
            networkids=private_networks,
            startvm=start,
        )["virtualmachine"]

        if teardown:
            instances.append(instance)

        return instance

    yield _instance

    for instance in instances:
        exo.compute.cs.destroyVirtualMachine(id=instance["id"])


@pytest.fixture(autouse=True, scope="function")
def privnet(exo, zone, test_prefix, test_description):
    private_networks = []

    def _private_network(
        name=None,
        description=test_description,
        zone_id=_DEFAULT_ZONE_ID,
        start_ip=None,
        end_ip=None,
        netmask=None,
        teardown=True,
    ):
        private_network = exo.compute.cs.createNetwork(
            zoneid=zone_id,
            name=name if name else "-".join([test_prefix, _random_str()]),
            displaytext=description,
            startip=start_ip,
            endip=end_ip,
            netmask=netmask,
        )["network"]

        if teardown:
            private_networks.append(private_network)

        return private_network

    yield _private_network

    for private_network in private_networks:
        res = exo.compute.cs.deleteNetwork(id=private_network["id"])
        assert res["success"]


@pytest.fixture(autouse=True, scope="function")
def sg(exo, test_prefix, test_description):
    security_groups = []

    def _security_group(name=None, description=test_description, teardown=True):
        security_group = exo.compute.cs.createSecurityGroup(
            name=name if name else "-".join([test_prefix, _random_str()]),
            description=description,
        )["securitygroup"]

        if teardown:
            security_groups.append(security_group)

        return security_group

    yield _security_group

    for security_group in security_groups:
        # We check if there are instances still using the SG before trying to deleteing
        # it: since it's not possible to delete a referenced SG we wait for a while
        # before trying and hope for the best...
        res = exo.compute.cs.deleteSecurityGroup(id=security_group["id"])
        assert res["success"]


@pytest.fixture(autouse=True, scope="function")
def sshkey(exo, test_prefix):
    ssh_keys = []

    def _ssh_key(name=None, teardown=True):
        ssh_key = exo.compute.cs.createSSHKeyPair(
            name=name if name else "-".join([test_prefix, _random_str()])
        )["keypair"]

        if teardown:
            ssh_keys.append(ssh_key)

        return ssh_key

    yield _ssh_key

    for ssh_key in ssh_keys:
        res = exo.compute.cs.deleteSSHKeyPair(name=ssh_key["name"])
        assert res["success"]


@pytest.fixture(autouse=True, scope="function")
def domain(exo, test_prefix):
    domains = []

    def _domain(name=None, teardown=True):
        domain = exo.dns.cs.createDnsDomain(
            name="-".join([test_prefix, _random_str()]) + ".net"
        )["dnsdomain"]

        if teardown:
            domains.append(domain)

        return domain

    yield _domain

    for domain in domains:
        res = exo.dns.cs.deleteDnsDomain(id=domain["id"])
        assert res["success"]


@pytest.fixture(autouse=True, scope="function")
def bucket(exo, test_prefix):
    buckets = []

    def _bucket(name=None, zone=None, acl="private", teardown=True):
        bucket = exo.storage.boto.create_bucket(
            Bucket=name if name else "-".join([test_prefix, _random_str()]),
            CreateBucketConfiguration={
                "LocationConstraint": _DEFAULT_ZONE_NAME if zone is None else zone
            },
            ACL=acl,
        )["Location"].lstrip("/")

        if teardown:
            buckets.append(bucket)

        return bucket

    yield _bucket

    for bucket in buckets:
        res = exo.storage.boto.delete_bucket(Bucket=bucket)


@pytest.fixture(autouse=True, scope="function")
def runstatus_page(exo, test_prefix):
    pages = []

    def _page(name=None, teardown=True):
        name = name if name else "-".join([test_prefix, _random_str()])
        page = exo.runstatus._post(
            url="/pages", json={"name": name, "subdomain": name}
        ).json()

        if teardown:
            pages.append(page)

        return page

    yield _page

    for page in pages:
        res = exo.runstatus._delete(url="/pages/{p}".format(p=page["subdomain"]))
