#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from cs import CloudStackApiException
from exoscale.api import ResourceNotFoundError
from exoscale.api.compute import *
from .conftest import _random_str


class TestCompute:
    ### Anti-Affinity Group

    def test_create_anti_affinity_group(self, exo, test_prefix, test_description):
        anti_affinity_group_name = "-".join([test_prefix, _random_str()])
        anti_affinity_group = exo.compute.create_anti_affinity_group(
            name=anti_affinity_group_name, description=test_description
        )
        assert anti_affinity_group.id != ""
        assert anti_affinity_group.name == anti_affinity_group_name
        assert anti_affinity_group.description == test_description

        exo.compute.cs.deleteAffinityGroup(id=anti_affinity_group.id)

    def test_list_anti_affinity_groups(self, exo, aag):
        anti_affinity_group = AntiAffinityGroup.from_cs(exo.compute, aag())

        anti_affinity_groups = list(exo.compute.list_anti_affinity_groups())
        # We cannot guarantee that there will be only our resources,
        # so we ensure we get at least our fixture anti-affinity group
        assert len(anti_affinity_groups) >= 1

    def test_get_anti_affinity_group(self, exo, aag):
        anti_affinity_group1 = AntiAffinityGroup.from_cs(exo.compute, aag())
        anti_affinity_group2 = AntiAffinityGroup.from_cs(exo.compute, aag())

        anti_affinity_group = exo.compute.get_anti_affinity_group(
            id=anti_affinity_group1.id
        )
        assert anti_affinity_group.id == anti_affinity_group1.id

        anti_affinity_group = exo.compute.get_anti_affinity_group(
            name=anti_affinity_group2.name
        )
        assert anti_affinity_group.id == anti_affinity_group2.id

        with pytest.raises(ResourceNotFoundError) as excinfo:
            anti_affinity_group = exo.compute.get_anti_affinity_group(
                id="00000000-0000-0000-0000-000000000000"
            )
            assert anti_affinity_group is None
        assert excinfo.type == ResourceNotFoundError

        with pytest.raises(ResourceNotFoundError) as excinfo:
            anti_affinity_group = exo.compute.get_anti_affinity_group(name="lolnope")
            assert anti_affinity_group is None
        assert excinfo.type == ResourceNotFoundError

    ### Elastic IP

    def test_create_elastic_ip(self, exo, zone):
        zone_gva2 = Zone.from_cs(zone("ch-gva-2"))
        healthcheck_mode = "http"
        healthcheck_port = 80
        healthcheck_path = "/health"
        healthcheck_interval = 5
        healthcheck_timeout = 3
        healthcheck_strikes_ok = 2
        healthcheck_strikes_fail = 1

        elastic_ip = exo.compute.create_elastic_ip(
            zone=zone_gva2,
            healthcheck_mode=healthcheck_mode,
            healthcheck_port=healthcheck_port,
            healthcheck_path=healthcheck_path,
            healthcheck_interval=healthcheck_interval,
            healthcheck_timeout=healthcheck_timeout,
            healthcheck_strikes_ok=healthcheck_strikes_ok,
            healthcheck_strikes_fail=healthcheck_strikes_fail,
        )
        assert elastic_ip.zone.id == zone_gva2.id
        assert elastic_ip.zone.name == zone_gva2.name
        assert elastic_ip.address != ""
        assert elastic_ip.healthcheck_mode == healthcheck_mode
        assert elastic_ip.healthcheck_port == healthcheck_port
        assert elastic_ip.healthcheck_path == healthcheck_path
        assert elastic_ip.healthcheck_interval == healthcheck_interval
        assert elastic_ip.healthcheck_timeout == healthcheck_timeout
        assert elastic_ip.healthcheck_strikes_ok == healthcheck_strikes_ok
        assert elastic_ip.healthcheck_strikes_fail == healthcheck_strikes_fail

        exo.compute.cs.disassociateIpAddress(id=elastic_ip.id)

    def test_list_elastic_ips(self, exo, zone, eip):
        zone_gva2 = Zone.from_cs(zone("ch-gva-2"))
        zone_fra1 = Zone.from_cs(zone("de-fra-1"))
        elastic_ip1 = eip(zone_id=zone_gva2.id)
        elastic_ip2 = eip(zone_id=zone_fra1.id)

        elastic_ips = list(exo.compute.list_elastic_ips())
        # We cannot guarantee that there will be only our resources,
        # so we ensure we get at least our fixture Elastic IPs
        assert len(elastic_ips) >= 2

        elastic_ips = list(exo.compute.list_elastic_ips(zone=zone_gva2))
        # We cannot guarantee that there will be only our resources,
        # so we ensure we get at least our fixture Elastic IP
        assert len(elastic_ips) >= 1

    def test_get_elastic_ip(self, exo, zone, eip):
        elastic_ip1 = ElasticIP.from_cs(exo.compute, eip())
        elastic_ip2 = ElasticIP.from_cs(exo.compute, eip())

        elastic_ip = exo.compute.get_elastic_ip(id=elastic_ip1.id)
        assert elastic_ip.id == elastic_ip1.id

        elastic_ip = exo.compute.get_elastic_ip(address=elastic_ip2.address)
        assert elastic_ip.id == elastic_ip2.id

        with pytest.raises(ResourceNotFoundError) as excinfo:
            elastic_ip = exo.compute.get_elastic_ip(
                id="00000000-0000-0000-0000-000000000000"
            )
            assert elastic_ip is None
        assert excinfo.type == ResourceNotFoundError

        with pytest.raises(ResourceNotFoundError) as excinfo:
            elastic_ip = exo.compute.get_elastic_ip(address="1.2.3.4")
            assert elastic_ip is None
        assert excinfo.type == ResourceNotFoundError

    ### Instance

    def test_create_instance(
        self,
        exo,
        zone,
        aag,
        sg,
        privnet,
        sshkey,
        instance_type,
        instance_template,
        test_prefix,
        test_instance_service_offering_id,
        test_instance_template_id,
    ):
        zone_gva2 = Zone.from_cs(zone("ch-gva-2"))
        instance_name = "-".join([test_prefix, _random_str()])
        instance_type = InstanceType.from_cs(
            instance_type(id=test_instance_service_offering_id)
        )
        template = InstanceTemplate.from_cs(
            exo.compute, instance_template(id=test_instance_template_id)
        )
        anti_affinity_group = AntiAffinityGroup.from_cs(exo.compute, aag())
        private_network = PrivateNetwork.from_cs(exo.compute, privnet())
        security_group1 = SecurityGroup.from_cs(exo.compute, sg())
        security_group2 = SecurityGroup.from_cs(exo.compute, sg())
        ssh_key = SSHKey.from_cs(exo.compute, sshkey())

        instance = exo.compute.create_instance(
            name=instance_name,
            zone=zone_gva2,
            type=instance_type,
            template=template,
            root_disk_size=20,
            security_groups=[security_group1, security_group2],
            anti_affinity_groups=[anti_affinity_group],
            private_networks=[private_network],
            enable_ipv6=True,
            ssh_key=ssh_key,
        )
        assert instance.id != ""
        assert instance.name == instance_name
        assert instance.zone.id == zone_gva2.id
        assert instance.type.id == instance_type.id
        assert instance.template.id == template.id
        assert instance.volume_size == 21474836480  # 20 GB
        assert instance.ipv4_address != ""
        assert instance.ipv6_address != ""
        assert instance.ssh_key.name == ssh_key.name
        assert (
            list(i["name"] for i in instance.res["securitygroup"]).sort()
            == [security_group1.name, security_group2.name].sort()
        )
        assert instance.res["affinitygroup"][0]["id"] == anti_affinity_group.id
        assert (
            list(i for i in instance.res["nic"] if not i["isdefault"])[0]["networkid"]
            == private_network.id
        )

        exo.compute.cs.destroyVirtualMachine(id=instance.id)

    def test_list_instances(self, exo, zone, privnet, instance):
        zone_gva2 = Zone.from_cs(zone("ch-gva-2"))
        zone_fra1 = Zone.from_cs(zone("de-fra-1"))
        private_network = PrivateNetwork.from_cs(exo.compute, privnet())
        instance1 = Instance.from_cs(exo.compute, instance(zone_id=zone_gva2.id))
        instance2 = Instance.from_cs(exo.compute, instance(zone_id=zone_fra1.id))

        instances = list(exo.compute.list_instances(zone=zone_gva2))
        # We cannot guarantee that there will be only our resources,
        # so we ensure we get at least our fixture instance
        assert len(instances) >= 1

        instances = list(exo.compute.list_instances(name=instance1.name))
        assert len(instances) == 1

        instances = list(exo.compute.list_instances(ids=[instance1.id, instance2.id]))
        assert len(instances) == 2

        res = exo.compute.cs.addNicToVirtualMachine(
            virtualmachineid=instance1.id, networkid=private_network.id
        )

        instances = list(exo.compute.list_instances(networkid=private_network.id))
        assert len(instances) == 1

        for nic in res["virtualmachine"]["nic"]:
            if nic["isdefault"]:
                continue
            exo.compute.cs.removeNicFromVirtualMachine(
                virtualmachineid=instance1.id, nicid=nic["id"]
            )

    def test_get_instance(self, exo, privnet, instance):
        private_network = PrivateNetwork.from_cs(exo.compute, privnet())
        instance1 = Instance.from_cs(exo.compute, instance())

        instance = exo.compute.get_instance(id=instance1.id)
        assert instance.id == instance1.id

        instance = exo.compute.get_instance(ip_address=instance1.ipv4_address)
        assert instance.id == instance1.id

        with pytest.raises(ResourceNotFoundError) as excinfo:
            instance = exo.compute.get_instance(
                id="00000000-0000-0000-0000-000000000000"
            )
            assert instance is None
        assert excinfo.type == ResourceNotFoundError

    ### Instance Template

    def test_list_instance_templates(
        self, exo, zone, test_instance_template_id, test_instance_template_name
    ):
        zone_gva2 = Zone.from_cs(zone("ch-gva-2"))

        instance_templates = list(exo.compute.list_instance_templates(zone=zone_gva2))
        assert len(instance_templates) > 10

        instance_templates = list(
            exo.compute.list_instance_templates(
                name=test_instance_template_name, zone=zone_gva2
            )
        )
        assert len(instance_templates) == 1

    def test_get_instance_template(self, exo, test_instance_template_id):
        instance_template = exo.compute.get_instance_template(
            id=test_instance_template_id
        )
        assert instance_template.id == test_instance_template_id

        with pytest.raises(ResourceNotFoundError) as excinfo:
            instance_template = exo.compute.get_instance_template(
                id="00000000-0000-0000-0000-000000000000"
            )
            assert instance_template is None
        assert excinfo.type == ResourceNotFoundError

    ### Instance Type

    def test_list_instance_types(self, exo):
        expected_type_name = "Micro"
        expected_type_id = "71004023-bb72-4a97-b1e9-bc66dfce9470"  # Micro
        expected_types = [
            "Micro",
            "Tiny",
            "Small",
            "Medium",
            "Large",
            "Extra-large",
            "Huge",
            "Mega",
            "Titan",
            "Jumbo",
        ]

        types = list(exo.compute.list_instance_types())
        assert len(types) > len(expected_types)

    def test_get_instance_type(self, exo):
        expected_type_name = "Micro"
        expected_type_id = "71004023-bb72-4a97-b1e9-bc66dfce9470"  # Micro

        instance_type = exo.compute.get_instance_type(name=expected_type_name)
        assert instance_type.name == expected_type_name
        assert instance_type.id == expected_type_id

        instance_type = exo.compute.get_instance_type(id=expected_type_id)
        assert instance_type.name == expected_type_name
        assert instance_type.id == expected_type_id

        with pytest.raises(ResourceNotFoundError) as excinfo:
            instance_type = exo.compute.get_instance_type(
                id="00000000-0000-0000-0000-000000000000"
            )
            assert instance_type is None
        assert excinfo.type == ResourceNotFoundError

        with pytest.raises(ResourceNotFoundError) as excinfo:
            instance_type = exo.compute.get_instance_type(name="lolnope")
            assert instance_type is None
        assert excinfo.type == ResourceNotFoundError

    ### Private Network

    def test_create_private_network(self, exo, zone, test_prefix, test_description):
        private_network_name = "-".join([test_prefix, _random_str()])
        zone_gva2 = Zone.from_cs(zone("ch-gva-2"))
        start_ip = "192.168.1.10"
        end_ip = "192.168.1.100"
        netmask = "255.255.255.0"

        private_network = exo.compute.create_private_network(
            zone=zone_gva2,
            name=private_network_name,
            description=test_description,
            start_ip=start_ip,
            end_ip=end_ip,
            netmask=netmask,
        )
        assert private_network.zone.id == zone_gva2.id
        assert private_network.zone.name == zone_gva2.name
        assert private_network.name == private_network_name
        assert private_network.description == test_description
        assert private_network.start_ip == start_ip
        assert private_network.end_ip == end_ip
        assert private_network.netmask == netmask

        exo.compute.cs.deleteNetwork(id=private_network.id)

    def test_list_private_networks(self, exo, zone, privnet):
        zone_gva2 = Zone.from_cs(zone("ch-gva-2"))
        zone_fra1 = Zone.from_cs(zone("de-fra-1"))
        private_network1 = PrivateNetwork.from_cs(
            exo.compute, privnet(zone_id=zone_gva2.id)
        )
        private_network2 = PrivateNetwork.from_cs(
            exo.compute, privnet(zone_id=zone_fra1.id)
        )

        private_networks = list(exo.compute.list_private_networks())
        # We cannot guarantee that there will be only our resources,
        # so we ensure we get at least our 2 fixture private networks
        assert len(private_networks) >= 2

        private_networks = list(
            exo.compute.list_private_networks(name=private_network1.name)
        )
        assert len(private_networks) == 1
        assert private_networks[0].name == private_network1.name

        private_networks = list(exo.compute.list_private_networks(zone=zone_gva2))
        # We cannot guarantee that there will be only our resources,
        # so we ensure we get only private networks in the zone specified
        for p in private_networks:
            assert p.zone.name == private_network1.zone.name

    def test_get_private_network(self, exo, privnet):
        private_network1 = PrivateNetwork.from_cs(exo.compute, privnet())

        private_network = exo.compute.get_private_network(id=private_network1.id)
        assert private_network.id == private_network1.id

        with pytest.raises(ResourceNotFoundError) as excinfo:
            private_network = exo.compute.get_private_network(
                id="00000000-0000-0000-0000-000000000000"
            )
            assert private_network is None
        assert excinfo.type == ResourceNotFoundError

    ### Security Group

    def test_create_security_group(self, exo, test_prefix, test_description):
        security_group_name = "-".join([test_prefix, _random_str()])

        security_group = exo.compute.create_security_group(
            name=security_group_name, description=test_description
        )

        assert security_group.id != ""
        assert security_group.name == security_group_name
        assert security_group.description == test_description

        exo.compute.cs.deleteSecurityGroup(id=security_group.id)

    def test_list_security_groups(self, exo, sg):
        security_group1 = SecurityGroup.from_cs(exo.compute, sg())
        security_group2 = SecurityGroup.from_cs(exo.compute, sg())

        security_groups = list(exo.compute.list_security_groups())
        # We cannot guarantee that there will be only our resources,
        # so we ensure we get at least our 2 fixture security groups
        assert len(security_groups) >= 2

    def test_get_security_group(self, exo, sg):
        security_group1 = SecurityGroup.from_cs(exo.compute, sg())
        security_group2 = SecurityGroup.from_cs(exo.compute, sg())

        security_group = exo.compute.get_security_group(id=security_group1.id)
        assert security_group.name == security_group1.name
        assert security_group.description == security_group1.description

        security_group = exo.compute.get_security_group(name=security_group2.name)
        assert security_group.name == security_group2.name
        assert security_group.description == security_group2.description

        with pytest.raises(ResourceNotFoundError) as excinfo:
            security_group = exo.compute.get_security_group(
                id="00000000-0000-0000-0000-000000000000"
            )
            assert security_group is None
        assert excinfo.type == ResourceNotFoundError

        with pytest.raises(ResourceNotFoundError) as excinfo:
            security_group = exo.compute.get_security_group(name="lolnope")
            assert security_group is None
        assert excinfo.type == ResourceNotFoundError

    ### SSH Key

    def test_create_ssh_key(self, exo, test_prefix):
        ssh_key_name = "-".join([test_prefix, _random_str()])

        ssh_key = exo.compute.create_ssh_key(name=ssh_key_name)

        assert ssh_key.name == ssh_key_name
        assert ssh_key.fingerprint != ""
        assert ssh_key.private_key != ""

        exo.compute.cs.deleteSSHKeyPair(name=ssh_key.name)

    def test_register_ssh_key(self, exo, test_prefix):
        ssh_key_name = "-".join([test_prefix, _random_str()])

        ssh_key = exo.compute.register_ssh_key(
            name=ssh_key_name,
            public_key="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDGRYWaNYBG/Ld3ZnXGsK9p"
            + "Zl9kT3B6GXvsslgy/LCjkJvDIP+nL+opAArKZD1P1+SGylCLt8ISdJNNGLtxKp9CL12EG"
            + "AYqdDvm5PurkpqIkEsfhsIG4dne9hNu7ZW8aHGHDWM62/4uiWOKtbGdv/P33L/Fepzypw"
            + "pivFsaXwPYVunAgoBQLUAmj/xcwtx7cvKS4zdj0+Iu21CIGU9wsH3ZLS34QiXtCGJyMOp"
            + "158qld9Oeus3Y/7DQ4w5XvfGn9sddxHOSMwUlNiFVty673X3exgMIc8psZOsHvWZPS0zW"
            + "x9gEDE95cUU10K6u4vzTr2O6fgDOQBynEUw3CDiHvwRD alice@example.net",
        )

        assert ssh_key.name == ssh_key_name
        assert ssh_key.fingerprint == "a0:25:fa:32:c0:18:7a:f8:e8:b2:3b:30:d8:ca:9a:2e"

        exo.compute.cs.deleteSSHKeyPair(name=ssh_key.name)

    def test_list_ssh_keys(self, exo, sshkey):
        ssh_key = SSHKey.from_cs(exo.compute, sshkey())

        ssh_keys = list(exo.compute.list_ssh_keys())
        # We cannot guarantee that there will be only our resources,
        # so we ensure we get at least our fixture SSH key
        assert len(ssh_keys) >= 1

    def test_get_ssh_key(self, exo, sshkey):
        ssh_key = SSHKey.from_cs(exo.compute, sshkey())

        ssh_key = exo.compute.get_ssh_key(name=ssh_key.name)
        assert ssh_key.name == ssh_key.name

        with pytest.raises(ResourceNotFoundError) as excinfo:
            ssh_key = exo.compute.get_ssh_key(name="lolnope")
            assert sshkey is None
        assert excinfo.type == ResourceNotFoundError

    ### Zone

    def test_list_zones(self, exo):
        expected_zones = [
            "at-vie-1",
            "bg-sof-1",
            "ch-dk-2",
            "ch-gva-2",
            "de-fra-1",
            "de-muc-1",
        ]

        zones = list(exo.compute.list_zones())
        assert len(zones) >= len(expected_zones)

    def test_get_zone(self, exo):
        expected_zone_name = "ch-gva-2"
        expected_zone_id = "1128bd56-b4d9-4ac6-a7b9-c715b187ce11"

        zone = exo.compute.get_zone(id=expected_zone_id)
        assert zone.name == expected_zone_name
        assert zone.id == expected_zone_id

        zone = exo.compute.get_zone(name=expected_zone_name)
        assert zone.name == expected_zone_name
        assert zone.id == expected_zone_id
