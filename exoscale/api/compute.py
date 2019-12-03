# -*- coding: utf-8 -*-

"""
This submodule represents the Exoscale Compute API.
"""

import attr
from . import API, Resource, APIException, ResourceNotFoundError
from base64 import b64encode
from cs import CloudStack, CloudStackApiException
from datetime import datetime
import time


@attr.s
class AntiAffinityGroup(Resource):
    """
    An Anti-Affinity Group.

    Attributes:
        id (str): the Anti-Affinity Group unique identifier
        name (str): the Anti-Affinity Group display name
        description (str): the Anti-Affinity Group description
    """

    compute = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    name = attr.ib()
    description = attr.ib(default="", repr=False)

    @classmethod
    def _from_cs(cls, compute, res):
        return cls(
            compute,
            res,
            id=res["id"],
            name=res["name"],
            description=res.get("description", ""),
        )

    def delete(self):
        """
        Delete the Anti-Affinity Group.

        Returns:
            None
        """

        try:
            self.compute.cs.deleteAffinityGroup(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.compute = None
        self.res = None
        self.id = None
        self.name = None
        self.description = None


@attr.s
class ElasticIP(Resource):
    """
    An Elastic IP.

    Attributes:
        id (str): the Elastic IP unique identifier
        zone (Zone): the zone in which the Elastic IP is located
        address (str): the Elastic IP address
        description (str): the Elastic IP description
        healthcheck_mode (str): the healthcheck probing mode (must be either "tcp" or
            "http")
        healthcheck_port (int): the healthcheck service port to probe
        healthcheck_path (str): the healthcheck probe HTTP request path (must be
            specified in http mode)
        healthcheck_interval (int): the healthcheck probing interval in seconds
        healthcheck_timeout (int): the time in seconds before considering a healthcheck
            probing failed
        healthcheck_strikes_ok (int): the number of successful healthcheck probes before
            considering the target healthy
        healthcheck_strikes_fail (int): the number of unsuccessful healthcheck probes
            before considering the target unhealthy
    """

    compute = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    zone = attr.ib(repr=False)
    address = attr.ib()
    description = attr.ib(default=None, repr=False)
    healthcheck_mode = attr.ib(default=None, repr=False)
    healthcheck_port = attr.ib(default=None, repr=False)
    healthcheck_path = attr.ib(default=None, repr=False)
    healthcheck_interval = attr.ib(default=None, repr=False)
    healthcheck_timeout = attr.ib(default=None, repr=False)
    healthcheck_strikes_ok = attr.ib(default=None, repr=False)
    healthcheck_strikes_fail = attr.ib(default=None, repr=False)

    @classmethod
    def _from_cs(cls, compute, res, zone=None):
        if zone is None:
            zone = compute.get_zone(id=res["zoneid"])

        return cls(
            compute,
            res,
            id=res["id"],
            zone=zone,
            address=res["ipaddress"],
            description=res["description"],
            healthcheck_mode=res.get("healthcheck", {}).get("mode", None),
            healthcheck_port=res.get("healthcheck", {}).get("port", None),
            healthcheck_path=res.get("healthcheck", {}).get("path", None),
            healthcheck_interval=res.get("healthcheck", {}).get("interval", None),
            healthcheck_timeout=res.get("healthcheck", {}).get("timeout", None),
            healthcheck_strikes_ok=res.get("healthcheck", {}).get("strikes-ok", None),
            healthcheck_strikes_fail=res.get("healthcheck", {}).get(
                "strikes-fail", None
            ),
        )

    @property
    def instances(self):
        """
        Instances the Elastic IP is attached to.

        Yields:
            Instance: the next instance the Elastic IP is attached to

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        for instance in self.compute.list_instances(zone=self.zone):
            for nic in instance.res.get("nic", []):
                if nic["isdefault"] and self.address in list(
                    a["ipaddress"] for a in nic.get("secondaryip", [])
                ):
                    yield instance

    @property
    def reverse_dns(self):
        """
        The reverse DNS currently set on the Elastic IP.

        Returns:
            str: reverse DNS record, or None if none set

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            res = self.compute.cs.queryReverseDnsForPublicIpAddress(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        if res["publicipaddress"]["reversedns"]:
            return res["publicipaddress"]["reversedns"][0]["domainname"]

    def update(
        self,
        description=None,
        healthcheck_mode=None,
        healthcheck_port=None,
        healthcheck_path=None,
        healthcheck_interval=None,
        healthcheck_timeout=None,
        healthcheck_strikes_ok=None,
        healthcheck_strikes_fail=None,
    ):
        """
        Update the Elastic IP properties.

        Parameters:
            description (str): the Elastic IP description
            healthcheck_mode (str): the healthcheck probing mode (must be either "tcp"
                or "http")
            healthcheck_port (int): the healthcheck service port to probe
            healthcheck_path (str): the healthcheck probe HTTP request path (must be
                specified in http mode)
            healthcheck_interval (int): the healthcheck probing interval in seconds
            healthcheck_timeout (int): the time in seconds before considering a
                healthcheck probing failed
            healthcheck_strikes_ok (int): the number of successful healthcheck probes
                before considering the target healthy
            healthcheck_strikes_fail (int): the number of unsuccessful healthcheck
                probes before considering the target unhealthy

        Returns
            None
        """

        try:
            # We have to pass function arguments using **kwargs form because
            # of the hyphen in "strikes-ok"/"strikes-fail" arguments.
            self.compute.cs.updateIpAddress(
                **{
                    "id": self.id,
                    "description": description,
                    "mode": healthcheck_mode,
                    "port": healthcheck_port,
                    "path": healthcheck_path,
                    "interval": healthcheck_interval,
                    "timeout": healthcheck_timeout,
                    "strikes-ok": healthcheck_strikes_ok,
                    "strikes-fail": healthcheck_strikes_fail,
                }
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.description = description if description else self.description
        self.healthcheck_mode = (
            healthcheck_mode if healthcheck_mode else self.healthcheck_mode
        )
        self.healthcheck_port = (
            healthcheck_port if healthcheck_port else self.healthcheck_port
        )
        self.healthcheck_path = (
            healthcheck_path if healthcheck_path else self.healthcheck_path
        )
        self.healthcheck_interval = (
            healthcheck_interval if healthcheck_interval else self.healthcheck_interval
        )
        self.healthcheck_timeout = (
            healthcheck_timeout if healthcheck_timeout else self.healthcheck_timeout
        )
        self.healthcheck_strikes_ok = (
            healthcheck_strikes_ok
            if healthcheck_strikes_ok
            else self.healthcheck_strikes_ok
        )
        self.healthcheck_strikes_fail = (
            healthcheck_strikes_fail
            if healthcheck_strikes_fail
            else self.healthcheck_strikes_fail
        )

    def attach_instance(self, instance):
        """
        Attach the Elastic IP to a Compute instance.

        Parameters:
            instance (Instance): the instance to attach the Elastic IP to

        Returns:
            None
        """

        instance.attach_elastic_ip(elastic_ip=self)

    def detach_instance(self, instance):
        """
        Detach the Elastic IP from a Compute instance it is attached to.

        Parameters:
            instance (Instance): the instance to detach the Elastic IP from

        Returns:
            None
        """

        instance.detach_elastic_ip(elastic_ip=self)

    def set_reverse_dns(self, record):
        """
        Set the Elastic IP address reverse DNS record.

        Parameters:
            record (str): the reverse DNS record to set

        Returns:
            None
        """

        try:
            self.compute.cs.updateReverseDnsForPublicIpAddress(
                id=self.id, domainname=record
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def unset_reverse_dns(self):
        """
        Unset the Elastic IP address reverse DNS record.

        Returns:
            None
        """

        try:
            self.compute.cs.deleteReverseDnsFromPublicIpAddress(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def delete(self, detach_instances=False):
        """
        Delete the Elastic IP.

        Parameters:
            detach_instances (bool): a flag indicating whether to detach the Elastic
                IP from the instances before deleting it

        Returns:
            None
        """

        try:
            if detach_instances:
                for instance in self.instances:
                    self.detach_instance(instance)

            self.compute.cs.disassociateIpAddress(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.compute = None
        self.res = None
        self.id = None
        self.zone = None
        self.address = None
        self.description = None
        self.healthcheck_mode = None
        self.healthcheck_port = None
        self.healthcheck_path = None
        self.healthcheck_interval = None
        self.healthcheck_timeout = None
        self.healthcheck_strikes_ok = None
        self.healthcheck_strikes_fail = None


@attr.s
class Instance(Resource):
    """
    A Compute instance.

    Attributes:
        id (str): the instance unique identifier
        name (str): the instance hostname/display name
        creation_date (datetime.datetime): the instance creation date
        zone (Zone): the zone in which the instance is located
        type (InstanceType): the instance type
        template (InstanceTemplate): the instance template
        volume_size (int): the instance storage volume capacity in bytes
        ipv4_address (str): the instance public network interface IP address
        ipv6_address (str): the instance public network interface IPv6 address,
            or None if IPv6 is not enabled
        ssh_key (SSHKey): the SSH key installed in the instance user account,
        or None if no SSH key specified during instance creation
    """

    compute = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    name = attr.ib()
    creation_date = attr.ib(repr=False)
    zone = attr.ib(repr=False)
    type = attr.ib(repr=False)
    template = attr.ib(repr=False)
    volume_id = attr.ib(repr=False)
    volume_size = attr.ib(repr=False)
    ipv4_address = attr.ib(repr=False)
    ipv6_address = attr.ib(default=None, repr=False)
    ssh_key = attr.ib(default=None, repr=False)

    @classmethod
    def _from_cs(cls, compute, res, zone=None):
        if zone is None:
            zone = compute.get_zone(id=res["zoneid"])

        try:
            _list = compute.cs.listVolumes(virtualmachineid=res["id"], fetch_list=True)
            volume_res = _list[0]
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return cls(
            compute,
            res,
            id=res["id"],
            name=res["displayname"],
            creation_date=datetime.strptime(res["created"], "%Y-%m-%dT%H:%M:%S%z"),
            zone=zone,
            type=compute.get_instance_type(id=res["serviceofferingid"]),
            template=compute.get_instance_template(zone, id=res["templateid"]),
            volume_id=volume_res["id"],
            volume_size=volume_res["size"],
            ipv4_address=next(i for i in res["nic"] if i["isdefault"]).get(
                "ipaddress", None
            ),
            ipv6_address=next(i for i in res["nic"] if i["isdefault"]).get(
                "ip6address", None
            ),
            ssh_key=compute.get_ssh_key(name=res["keypair"])
            if "keypair" in res.keys()
            else None,
        )

    @property
    def anti_affinity_groups(self):
        """
        Anti-Affinity Groups the instance is member of.

        Yields:
            AntiAffinityGroup: the next Anti-Affinity Group the instance is member of

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            _list = self.compute.cs.listAffinityGroups(
                virtualmachineid=self.id, fetch_list=True
            )
            for i in _list:
                yield AntiAffinityGroup._from_cs(self, i)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    @property
    def elastic_ips(self):
        """
        Elastic IPs attached to the instance.

        Yields:
            ElasticIP: the next Elastic IP attached to the instance

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            # FIXME: use `iselastic=True` filter
            _list = self.compute.cs.listNics(virtualmachineid=self.id, fetch_list=True)
            default_nic = self._default_nic(_list)
            for a in default_nic.get("secondaryip", []):
                yield self.compute.get_elastic_ip(
                    zone=self.zone, address=a["ipaddress"]
                )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    @property
    def private_networks(self):
        """
        Private Networks the instance is member of.

        Yields:
            PrivateNetwork: the next Private Network the instance is member of

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            _list = self.compute.cs.listNics(virtualmachineid=self.id, fetch_list=True)
            for nic in _list:
                if nic["isdefault"]:
                    continue
                yield self.compute.get_private_network(
                    zone=self.zone, id=nic["networkid"]
                )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    @property
    def reverse_dns(self):
        """
        The reverse DNS currently set on the public network interface IP address.

        Returns:
            str: reverse DNS record, or None if none set

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            res = self.compute.cs.queryReverseDnsForVirtualMachine(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        reverse_dns = self._default_nic(res["virtualmachine"]["nic"])["reversedns"]
        if reverse_dns:
            return reverse_dns[0]["domainname"]

    @property
    def security_groups(self):
        """
        Security Groups the instance is member of.

        Yields:
            SecurityGroup: the next Security Group the instance is member of

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            _list = self.compute.cs.listSecurityGroups(
                virtualmachineid=self.id, fetch_list=True
            )
            for i in _list:
                yield SecurityGroup._from_cs(self, i)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    @property
    def volume_snapshots(self):
        """
        Snapshots of the instance storage volume.

        Yields:
            InstanceVolumeSnapshot: the next instance storage volume snapshot

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            _list = self.compute.cs.listSnapshots(
                volumeid=self.volume_id, fetch_list=True
            )
            for i in _list:
                yield InstanceVolumeSnapshot._from_cs(self.compute, i)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    @property
    def state(self):
        """
        State of the instance.

        Returns:
            str: the current instance state

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            [res] = self.compute.cs.listVirtualMachines(id=self.id, fetch_list=True)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return res["state"].lower()

    @property
    def instance_pool(self):
        """
        Instance Pool the instance is a member of.

        Returns:
            InstancePool: the Instance Pool the instance is member of

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        if self.res.get("manager") == "instancepool":
            return self.compute.get_instance_pool(self.res["managerid"], self.zone)

    def update(self, name=None, security_groups=None, user_data=None):
        """
        Update the instance properties.

        Parameters:
            name (str): an instance hostname/display name
            security_groups ([SecurityGroup]): a list of Security Groups the instance
                is member of
            user_data (str): a cloud-init user data configuration

        Returns:
            None
        """

        try:
            self.compute.cs.updateVirtualMachine(
                id=self.id,
                name=name if name is not None else None,
                displayname=name if name is not None else None,
                securitygroupids=list(i.id for i in security_groups)
                if security_groups
                else None,
                userdata=b64encode(bytes(user_data, encoding="utf-8"))
                if user_data
                else None,
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        if name is not None:
            self.name = name

    def scale(self, type):
        """
        Change the instance type.

        Parameters:
            type (InstanceType): the type to scale the instance to

        Returns:
            None
        """

        try:
            self.compute.cs.scaleVirtualMachine(id=self.id, serviceofferingid=type.id)
            self.type = type
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def start(self):
        """
        Start a stopped instance.

        Returns:
            None
        """

        try:
            self.compute.cs.startVirtualMachine(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def stop(self):
        """
        Stop a running instance.

        Returns:
            None
        """

        try:
            self.compute.cs.stopVirtualMachine(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def reboot(self):
        """
        Reboot a running instance.

        Returns:
            None
        """

        try:
            self.compute.cs.rebootVirtualMachine(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def resize_volume(self, size):
        """
        Resize the instance storage volume.

        Parameters:
            size (int): new instance storage volume size in GB (must be greater than
                current size)

        Returns:
            None
        """

        try:
            res = self.compute.cs.resizeVolume(id=self.volume_id, size=size)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.volume_size = res["volume"]["size"]

    def snapshot_volume(self):
        """
        Take a snapshot of the instance storage volume.

        Returns:
            InstanceVolumeSnapshot: the instance storage volume snapshot taken
        """

        try:
            res = self.compute.cs.createSnapshot(volumeid=self.volume_id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return InstanceVolumeSnapshot._from_cs(self.compute, res["snapshot"])

    def attach_elastic_ip(self, elastic_ip):
        """
        Attach an Elastic IP to the instance.

        Parameters:
            elastic_ip (ElasticIP): the Elastic IP to attach

        Returns:
            None
        """

        try:
            _list = self.compute.cs.listNics(virtualmachineid=self.id, fetch_list=True)
            default_nic = self._default_nic(_list)
            self.compute.cs.addIpToNic(
                nicid=default_nic["id"], ipaddress=elastic_ip.address
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def detach_elastic_ip(self, elastic_ip):
        """
        Detach an Elastic IP from the instance.

        Parameters:
            elastic_ip (ElasticIP): the Elastic IP to detach

        Returns:
            None
        """

        try:
            _list = self.compute.cs.listNics(virtualmachineid=self.id, fetch_list=True)
            default_nic = self._default_nic(_list)
            for a in default_nic.get("secondaryip", []):
                if a["ipaddress"] == elastic_ip.address:
                    self.compute.cs.removeIpFromNic(id=a["id"])
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def attach_private_network(self, private_network):
        """
        Attach the instance to a Private Network.

        Parameters:
            private_network (PrivateNetwork): the Private Network to attach to

        Returns:
            None
        """

        try:
            self.compute.cs.addNicToVirtualMachine(
                virtualmachineid=self.id, networkid=private_network.id
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def detach_private_network(self, private_network):
        """
        Detach the instance from a Private Network.

        Parameters:
            private_network (PrivateNetwork): the Private Network to detach from

        Returns:
            None
        """

        try:
            [res] = self.compute.cs.listNics(
                virtualmachineid=self.id, networkid=private_network.id, fetch_list=True
            )

            self.compute.cs.removeNicFromVirtualMachine(
                virtualmachineid=self.id, nicid=res["id"]
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def set_reverse_dns(self, record):
        """
        Set the public network interface IP address reverse DNS record.

        Parameters:
            record (str): the reverse DNS record to set

        Returns:
            None
        """

        try:
            self.compute.cs.updateReverseDnsForVirtualMachine(
                id=self.id, domainname=record
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def unset_reverse_dns(self):
        """
        Unset the public network interface IP address reverse DNS record.

        Returns:
            None
        """

        try:
            self.compute.cs.deleteReverseDnsFromVirtualMachine(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def delete(self):
        """
        Delete the instance.

        Returns:
            None
        """

        try:
            self.compute.cs.destroyVirtualMachine(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.compute = None
        self.res = None
        self.id = None
        self.name = None
        self.creation_date = None
        self.zone = None
        self.type = None
        self.template = None
        self.ipv4_address = None
        self.ipv6_address = None
        self.ssh_key = None

    def _default_nic(self, nics):
        for nic in nics:
            if nic["isdefault"]:
                return nic


@attr.s
class InstanceTemplate(Resource):
    """
    A Compute instance template.

    Attributes:
        id (str): the template unique identifier
        name (str): the template name
        description (str): the template description
        zone (Zone): the zone in which the template is located
        date (datetime.datetime): the template creation date
        size (int): the template disk size
        ssh_key_enabled (bool): a flag indicating whether the SSH key deployment is
            enabled
        password_reset_enabled (bool): a flag indicating whether the user password can
            be reset

    References:
        * `Python datetime module`_

        .. _Python datetime module: https://docs.python.org/3/library/datetime.html
    """

    compute = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    name = attr.ib()
    description = attr.ib(repr=False)
    zone = attr.ib(repr=False)
    date = attr.ib(repr=False)
    size = attr.ib(repr=False)
    ssh_key_enabled = attr.ib(default=True, repr=False)
    password_reset_enabled = attr.ib(default=True, repr=False)
    username = attr.ib(default=None, repr=False)

    @classmethod
    def _from_cs(cls, compute, res, zone=None):
        if zone is None:
            zone = compute.get_zone(id=res["zoneid"])

        return cls(
            compute,
            res,
            id=res["id"],
            name=res["name"],
            description=res.get("displaytext", ""),
            zone=zone,
            date=datetime.strptime(res["created"], "%Y-%m-%dT%H:%M:%S%z"),
            size=res["size"],
            username=res["details"].get("username", None),
            ssh_key_enabled=res["sshkeyenabled"],
            password_reset_enabled=res["passwordenabled"],
        )

    @classmethod
    def _register(
        cls,
        compute,
        name,
        url,
        checksum,
        zone,
        description=None,
        username=None,
        disable_ssh_key=False,
        disable_password_reset=False,
    ):
        templateDetails = {}
        if username is not None:
            templateDetails["username"] = username

        try:
            res = compute.cs.registerCustomTemplate(
                name=name,
                displaytext=description,
                zoneId=zone.id,
                url=url,
                checksum=checksum,
                details=templateDetails,
                sshkeyenabled=False if disable_ssh_key else True,
                passwordenabled=False if disable_password_reset else True,
                fetch_result=True,
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return cls._from_cs(compute, res["template"][0])

    def delete(self):
        """
        Delete the instance template.

        Returns:
            None
        """

        try:
            self.compute.cs.deleteTemplate(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.compute = None
        self.res = None
        self.name = None
        self.description = None
        self.zone = None
        self.date = None
        self.ssh_key_enabled = None
        self.password_reset_enabled = None
        self.username = None


@attr.s
class InstanceVolumeSnapshot(Resource):
    """
    A Compute instance storage volume snapshot.

    Attributes:
        id (str): the instance storage volume snapshot unique identifier
        date (datetime.datetime): the instance storage volume snapshot creation date
        size (int): the instance storage volume snapshot size in bytes

    References:
        * `Python datetime module`_

        .. _Python datetime module: https://docs.python.org/3/library/datetime.html
    """

    compute = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    date = attr.ib(repr=False)
    size = attr.ib(repr=False)

    @classmethod
    def _from_cs(cls, compute, res):
        return cls(
            compute,
            res,
            id=res["id"],
            date=datetime.strptime(res["created"], "%Y-%m-%dT%H:%M:%S%z"),
            size=res["size"],
        )

    @property
    def state(self):
        """
        State of the instance storage volume snapshot.

        Returns:
            str: the current instance storage volume snapshot state.

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            [res] = self.compute.cs.listSnapshots(id=self.id, fetch_list=True)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return res["state"].lower()

    def revert(self):
        """
        Revert the storage volume snapshot.

        Returns:
            None
        """

        try:
            res = self.compute.cs.revertSnapshot(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        if not res["success"]:
            raise APIException(reason=res["displaytext"])

    def delete(self):
        """
        Delete the storage volume snapshot.

        Returns:
            None
        """

        try:
            self.compute.cs.deleteSnapshot(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.compute = None
        self.res = None
        self.id = None
        self.date = None
        self.size = None


@attr.s
class InstanceType(Resource):
    """
    A Compute instance type.

    Attributes:
        id (str): the instance type unique identifier
        name (str): the instance type name
        cpu (int): the number of vCPU allocated
        memory (int): the amount of RAM allocated in MB
    """

    res = attr.ib(repr=False)
    id = attr.ib()
    name = attr.ib()
    cpu = attr.ib(repr=False)
    memory = attr.ib(repr=False)

    @classmethod
    def _from_cs(cls, res):
        return cls(
            res,
            id=res["id"],
            name=res["name"],
            cpu=res["cpunumber"],
            memory=res["memory"],
        )


@attr.s
class InstancePool(Resource):
    """
    A Compute Instance Pool.

    Attributes:
        id (str): the Instance Pool unique identifier
        name (str): the Instance Pool name
        description (str): the Instance Pool description
        zone (Zone): the zone in which the Instance Pool is located
        size (int): the number of Compute instance members the Instance Pool manages
        instance_type (InstanceType): the type of instances managed by this instance
            pool
        instance_template (InstanceTemplate): the template to be used when this instance
            pool creates new instances.
        instance_volume_size (int): the storage volume capacity in bytes to set when
            this Instance Pool creates new instances.
    """

    compute = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    name = attr.ib()
    zone = attr.ib(repr=False)
    size = attr.ib(repr=False)
    instance_type = attr.ib(repr=False)
    instance_template = attr.ib(repr=False)
    instance_volume_size = attr.ib(repr=False)
    description = attr.ib(default=None, repr=False)

    @classmethod
    def _from_cs(cls, compute, res, zone=None):
        if zone is None:
            zone = compute.get_zone(id=res["zoneid"])

        return cls(
            compute,
            res,
            id=res["id"],
            name=res["name"],
            description=res.get("description"),
            zone=zone,
            size=res["size"],
            instance_type=compute.get_instance_type(id=res["serviceofferingid"]),
            instance_template=compute.get_instance_template(zone, id=res["templateid"]),
            instance_volume_size=res["rootdisksize"],
        )

    @property
    def instances(self):
        """
        Pool instance members.

        Yields:
            Instance: the next instance managed by this pool

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            [res] = self.compute.cs.getInstancePool(
                id=self.id, zoneid=self.zone.id, fetch_list=True
            )
            for i in res.get("virtualmachines", []):
                yield Instance._from_cs(self.compute, i)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    @property
    def private_networks(self):
        """
        Private Networks the instances are member of.

        Yields:
            PrivateNetwork: the next Private Network the instances are member of

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            [res] = self.compute.cs.getInstancePool(
                id=self.id, zoneid=self.zone.id, fetch_list=True
            )
            for sgid in res.get("private_network_ids", []):
                yield self.compute.get_private_network(zone=self.zone, id=sgid)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    @property
    def state(self):
        """
        State of the Instance Pool.

        Returns:
            str: the current Instance Pool state.

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            [res] = self.compute.cs.getInstancePool(
                id=self.id, zoneid=self.zone.id, fetch_list=True
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return res["state"].lower()

    def scale(self, size):
        """
        Scale the Instance Pool up or down.

        Parameters:
            size (int): the number of Compute instance members the pool must manage

        Returns:
            None
        """

        if size <= 0:
            raise ValueError("size must be > 0")

        try:
            self.compute.cs.scaleInstancePool(
                id=self.id, zoneid=self.zone.id, size=size
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.size = size

    def update(
        self,
        name=None,
        description=None,
        instance_template=None,
        instance_volume_size=None,
        instance_user_data=None,
    ):
        """
        Update the Instance Pool properties.

        Parameters:
            name (str): an Instance Pool name
            description (str): an Instance Pool description
            instance_template (InstanceTemplate): an instance template to use for
                Compute instance members
            instance_volume_size (int): the Compute instance members storage volume
                size in GB
            instance_user_data (str): a cloud-init user data configuration to apply to
                the Compute instance members

        Returns:
            None
        """

        instance_template_id = None
        if instance_template is not None:
            instance_template_id = instance_template.id

        instance_user_data_content = None
        if instance_user_data is not None:
            instance_user_data_content = b64encode(
                bytes(instance_user_data, encoding="utf-8")
            )

        try:
            self.compute.cs.updateInstancePool(
                id=self.id,
                zoneid=self.zone.id,
                name=name,
                description=description,
                templateid=instance_template_id,
                rootdisksize=instance_volume_size,
                userdata=instance_user_data_content,
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        if name:
            self.name = name

        if description:
            self.description = description

        if instance_template is not None:
            self.instance_template = instance_template

        if instance_volume_size is not None:
            self.instance_volume_size = instance_volume_size

    def delete(self, wait=True, max_poll=300):
        """
        Delete the Instance Pool.

        Returns:
            None
        """

        try:
            self.compute.cs.destroyInstancePool(id=self.id, zoneid=self.zone.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        if wait:
            for _ in range(max_poll):
                time.sleep(1)
                try:
                    self.compute.cs.getInstancePool(id=self.id, zoneid=self.zone.id)
                except CloudStackApiException as e:
                    if e.error["errorcode"] == 404:
                        break
                    else:
                        raise APIException(e.error["errortext"], e.error)
        self.compute = None
        self.res = None
        self.id = None
        self.name = None
        self.zone = None
        self.size = None
        self.instance_type = None
        self.instance_template = None
        self.instance_volume_size = None


@attr.s
class PrivateNetwork(Resource):
    """
    A Private Network.

    Attributes:
        id (str): the Private Network unique identifier
        name (str): the Private Network name
        description (str): the Private Network description
        zone (Zone): the zone in which the Private Network is located
        start_ip (str): the start address of the managed Private Network IP range
        end_ip (str): the end address of the managed Private Network IP range
        netmask (str): the managed Private Network IP range netmask

    Note:
        The ``start_ip``, ``end_ip`` and ``netmask`` attributes are required in
        "managed" mode.
    """

    compute = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    name = attr.ib()
    zone = attr.ib(repr=False)
    description = attr.ib(default="", repr=False)
    start_ip = attr.ib(default=None, repr=False)
    end_ip = attr.ib(default=None, repr=False)
    netmask = attr.ib(default=None, repr=False)

    @classmethod
    def _from_cs(cls, compute, res, zone=None):
        if zone is None:
            zone = compute.get_zone(id=res["zoneid"])

        return cls(
            compute,
            res,
            id=res["id"],
            zone=zone,
            name=res["name"],
            description=res["displaytext"],
            start_ip=res.get("startip", ""),
            end_ip=res.get("endip", ""),
            netmask=res.get("netmask", ""),
        )

    @property
    def instances(self):
        """
        Private Network instance members.

        Yields:
            Instance: the next Private Network instance member

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        return self.compute.list_instances(zone=self.zone, networkid=self.id)

    def update(
        self, name=None, description=None, start_ip=None, end_ip=None, netmask=None
    ):
        """
        Update the Private Network properties.

        Parameters:
            name (str): a Private Network name
            description (str): a Private Network description
            start_ip (str): a start address of the managed Private Network IP range
            end_ip (str): an end address of the managed Private Network IP range
            netmask (str): a managed Private Network IP range netmask

        Returns:
            None
        """

        try:
            self.compute.cs.updateNetwork(
                id=self.id,
                name=name,
                displaytext=description,
                startip=start_ip,
                endip=end_ip,
                netmask=netmask,
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if start_ip is not None:
            self.start_ip = start_ip
        if end_ip is not None:
            self.end_ip = end_ip
        if netmask is not None:
            self.netmask = netmask

    def attach_instance(self, instance):
        """
        Attach a Compute instance to the Private Network.

        Parameters:
            instance (Instance): the instance to attach

        Returns:
            None
        """

        instance.attach_private_network(self)

    def detach_instance(self, instance):
        """
        Detach a Compute instance from the Private Network.

        Parameters:
            instances (Instance): the instance to detach

        Returns:
            None
        """

        instance.detach_private_network(self)

    def delete(self):
        """
        Delete the Private Network.

        Returns:
            None
        """

        try:
            self.compute.cs.deleteNetwork(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.compute = None
        self.res = None
        self.id = None
        self.name = None
        self.zone = None
        self.description = None
        self.start_ip = None
        self.end_ip = None
        self.netmask = None


@attr.s
class SecurityGroup(Resource):
    """
    A Security Group.

    Attributes:
        id (str): the Security Group unique identifier
        name (str): the Security Group name
        description (str): the Security Group description
    """

    compute = attr.ib(repr=False)
    res = attr.ib(repr=False)
    id = attr.ib()
    name = attr.ib()
    description = attr.ib(default="", repr=False)

    @classmethod
    def _from_cs(cls, compute, res):
        return cls(
            compute,
            res,
            id=res["id"],
            name=res["name"],
            description=res.get("description", ""),
        )

    @property
    def ingress_rules(self):
        """
        Ingress rules of the Security Group.

        Yields:
            SecurityGroupRule: the next ingress rule of the Security Group

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            [res] = self.compute.cs.listSecurityGroups(id=self.id, fetch_list=True)
            for rule in res.get("ingressrule", []):
                yield SecurityGroupRule._from_cs(
                    type="ingress", compute=self.compute, res=rule
                )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    @property
    def egress_rules(self):
        """
        Egress rules of the Security Group.

        Yields:
            SecurityGroupRule: the next egress rule of the Security Group

        Note:
            This property value is dynamically retrieved from the API, incurring extra
            latency.
        """

        try:
            [res] = self.compute.cs.listSecurityGroups(id=self.id, fetch_list=True)
            for rule in res.get("egressrule", []):
                yield SecurityGroupRule._from_cs(
                    type="egress", compute=self.compute, res=rule
                )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def add_rule(self, rule):
        """
        Add a rule to the Security Group.

        Parameters:
            rule (SecurityGroupRule): the Security Group rule to add

        Returns:
            None
        """

        if rule.type not in {"ingress", "egress"}:
            raise ValueError("rule type must be either ingress or egress")

        start_port, end_port = rule._parse_port()

        try:
            if rule.type == "ingress":
                self.compute.cs.authorizeSecurityGroupIngress(
                    securitygroupid=self.id,
                    description=rule.description,
                    cidrlist=rule.network_cidr,
                    startport=start_port,
                    endport=end_port,
                    icmpcode=rule.icmp_code,
                    icmptype=rule.icmp_type,
                    protocol=rule.protocol,
                    usersecuritygrouplist={"group": rule.security_group.name}
                    if rule.security_group
                    else None,
                )
            else:
                self.compute.cs.authorizeSecurityGroupEgress(
                    securitygroupid=self.id,
                    description=rule.description,
                    cidrlist=rule.network_cidr,
                    startport=start_port,
                    endport=end_port,
                    icmpcode=rule.icmp_code,
                    icmptype=rule.icmp_type,
                    protocol=rule.protocol,
                    usersecuritygrouplist={"group": rule.security_group.name}
                    if rule.security_group
                    else None,
                )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def delete(self):
        """
        Delete the Security Group.

        Returns:
            None
        """

        try:
            self.compute.cs.deleteSecurityGroup(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.compute = None
        self.res = None
        self.id = None
        self.name = None
        self.description = None


@attr.s
class SecurityGroupRule:
    """
    A Security Group rule.

    Attributes:
        id (str): the Security Group rule unique identifier
        type (str): the Security Group rule type (ingress or egress)
        description (str): the Security Group rule description
        network_cidr (str): a source/destination network CIDR to match
            (conflicts with security_group)
        security_group (SecurityGroup): a source/destination Security Group to match
            (conflicts with network_cidr)
        port (str): the source/destination port or port range to match
        protocol (str): a network protocol to match
        icmp_code (int): an ICMP code to match
        icmp_type (int): an ICMP type to match
    """

    type = attr.ib()
    compute = attr.ib(default=None, repr=False)
    id = attr.ib(default=None)
    description = attr.ib(default=None, repr=False)
    network_cidr = attr.ib(default=None, repr=False)
    security_group = attr.ib(default=None, repr=False)
    port = attr.ib(default=None, repr=False)
    protocol = attr.ib(default="tcp", repr=False)
    icmp_code = attr.ib(default=None, repr=False)
    icmp_type = attr.ib(default=None, repr=False)

    @classmethod
    def _from_cs(cls, compute, res, type):
        port = str(res.get("startport", ""))
        port = (
            "-".join([port, str(res["endport"])])
            if res.get("startport", None) is not None and str(res["endport"]) != port
            else port
        )

        return cls(
            type=type,
            compute=compute,
            id=res["ruleid"],
            description=res.get("description", None),
            network_cidr=res.get("cidr", None),
            security_group=compute.get_security_group(name=res["securitygroupname"])
            if "securitygroupname" in res
            else None,
            port=port,
            protocol=res.get("protocol", None),
            icmp_code=res.get("icmp_code", None),
            icmp_type=res.get("icmp_type", None),
        )

    @classmethod
    def ingress(cls, **kwargs):
        """
        Returns an ingress-type SecurityGroupRule object.
        
        Returns:
            SecurityGroupRule: an ingress-type Security Group rule

        See Also:
            See `SecurityGroupRule <#exoscale.api.compute.SecurityGroupRule>`_ class
            documentation for parameters.
        """

        return cls(type="ingress", **kwargs)

    @classmethod
    def egress(cls, **kwargs):
        """
        Returns an egress-type SecurityGroupRule object.
        
        Returns:
            SecurityGroupRule: an egress-type Security Group rule

        See Also:
            See `SecurityGroupRule <#exoscale.api.compute.SecurityGroupRule>`_ class
            documentation for parameters.
        """

        return cls(type="egress", **kwargs)

    def delete(self):
        """
        Delete the Security Group rule.

        Returns:
            None
        """

        try:
            if self.type == "ingress":
                self.compute.cs.revokeSecurityGroupIngress(id=self.id)
            else:
                self.compute.cs.revokeSecurityGroupEgress(id=self.id)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.type = None
        self.id = None
        self.description = None
        self.network_cidr = None
        self.security_group = None
        self.port = None
        self.protocol = None
        self.icmp_code = None
        self.icmp_type = None

    def _parse_port(self):
        """
        Parse the rule port attribute and returns a port range.

        Returns:
            int: start port
            int: end port
        """

        if not self.port:
            return None, None

        start_port, end_port = (
            self.port.split("-", maxsplit=1) if "-" in self.port else (self.port, None)
        )
        if not end_port:
            end_port = start_port

        return int(start_port), int(end_port)


@attr.s
class SSHKey(Resource):
    """
    A SSH key.

    Attributes:
        name (str): the SSH key unique name
        fingerprint (str): the SSH key fingerprint
        private_key (str): the SSH private key, or None if registered SSH key
    """

    compute = attr.ib(repr=False)
    res = attr.ib(repr=False)
    name = attr.ib()
    fingerprint = attr.ib()
    private_key = attr.ib(default=None, repr=False)

    @classmethod
    def _from_cs(cls, compute, res):
        return cls(
            compute,
            res,
            name=res["name"],
            fingerprint=res["fingerprint"],
            private_key=res.get("privatekey", None),
        )

    def delete(self):
        """
        Delete the SSH key.

        Returns:
            None
        """

        try:
            self.compute.cs.deleteSSHKeyPair(name=self.name)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.res = None
        self.name = None
        self.fingerprint = None
        self.private_key = None


@attr.s
class Zone(Resource):
    """
    An Exoscale zone.

    Attributes:
        id (str): the zone unique identifier
        name (str): the zone name
    """

    res = attr.ib(repr=False)
    id = attr.ib()
    name = attr.ib()

    @classmethod
    def _from_cs(cls, res):
        return cls(res, id=res["id"], name=res["name"])


class ComputeAPI(API):
    """
    An Exoscale Compute API client.

    Parameters:
        key (str): the Compute API key
        secret (str): the Compute API secret
        endpoint (str): the Compute API endpoint
        trace (bool): API request/response tracing flag
    """

    def __init__(
        self, key, secret, endpoint="https://api.exoscale.com/compute", trace=False
    ):
        super().__init__(endpoint, key, secret, trace)

        self.cs = CloudStack(
            key=key,
            secret=secret,
            endpoint=endpoint,
            session=self.session,
            headers={**self.session.headers, **{"User-Agent": self.user_agent}},
            trace=self.trace,
            fetch_result=True,
        )

    def __repr__(self):
        return "ComputeAPI(endpoint='{}' key='{}')".format(self.endpoint, self.key)

    def __str__(self):
        return self.__repr__()

    ### Anti-Affinity Group

    def create_anti_affinity_group(self, name, description=""):
        """
        Create an Anti-Affinity Group.

        Parameters:
            name (str): the Anti-Affinity Group name
            description (str): the Anti-Affinity Group description

        Returns:
            AntiAffinityGroup: the Anti-Affinity Group created
        """

        try:
            res = self.cs.createAffinityGroup(
                name=name, description=description, type="host anti-affinity"
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return AntiAffinityGroup._from_cs(self, res["affinitygroup"])

    def list_anti_affinity_groups(self, **kwargs):
        """
        List Anti-Affinity Groups.

        Yields:
            AntiAffinityGroup: the next Anti-Affinity Group
        """

        try:
            _list = self.cs.listAffinityGroups(fetch_list=True, **kwargs)

            for i in _list:
                if i["type"] == "host anti-affinity":
                    yield AntiAffinityGroup._from_cs(self, i)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def get_anti_affinity_group(self, name=None, id=None):
        """
        Get an Anti-Affinity Group.

        Parameters:
            id (str): an Anti-Affinity Group identifier
            name (str): an Anti-Affinity Group name

        Returns:
            AntiAffinityGroup: an Anti-Affinity Group
        """

        if id is None and name is None:
            raise ValueError("either id or name must be specifed")

        try:
            anti_affinity_groups = list(
                self.list_anti_affinity_groups(id=id, name=name)
            )
        except APIException as e:
            if "does not exist" in e.error["errortext"]:
                raise ResourceNotFoundError
            raise

        if len(anti_affinity_groups) == 0:
            raise ResourceNotFoundError

        return anti_affinity_groups[0]

    ### Elastic IP

    def create_elastic_ip(
        self,
        zone,
        description=None,
        healthcheck_mode=None,
        healthcheck_port=None,
        healthcheck_path="/",
        healthcheck_interval=10,
        healthcheck_timeout=2,
        healthcheck_strikes_ok=3,
        healthcheck_strikes_fail=2,
    ):
        """
        Create an Elastic IP.

        Parameters:
            zone (Zone): the zone in which to create the Elastic IP
            description (str): an Elastic IP description
            healthcheck_mode (str): optional healthcheck mode
            healthcheck_port (int): healthcheck port,
                required if healthchecking is enabled
            healthcheck_path (str): healthcheck probe HTTP request path,
                required in "http" mode
            healthcheck_interval (int): probe interval in seconds
            healthcheck_timeout (int): time in seconds before
                considering a probe failed, must be lower than interval
            healthcheck_strikes_ok (int): number of successful probes
                before considering the target healthy
            healthcheck_strikes_fail (int): number of unsuccessful probes
                before considering the target unhealthy

        Returns:
            ElasticIP: the Elastic IP created
        """

        # Unset healthcheck default values if healthchecking is not enabled
        if healthcheck_mode is None:
            healthcheck_path = None
            healthcheck_interval = None
            healthcheck_timeout = None
            healthcheck_strikes_ok = None
            healthcheck_strikes_fail = None

        try:
            # We have to pass function arguments using **kwargs form because
            # of the hyphen in "strikes-ok"/"strikes-fail" arguments.
            res = self.cs.associateIpAddress(
                **{
                    "zoneid": zone.id,
                    "description": description,
                    "mode": healthcheck_mode,
                    "port": healthcheck_port,
                    "path": healthcheck_path,
                    "interval": healthcheck_interval,
                    "timeout": healthcheck_timeout,
                    "strikes-ok": healthcheck_strikes_ok,
                    "strikes-fail": healthcheck_strikes_fail,
                }
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return ElasticIP._from_cs(self, res["ipaddress"], zone=zone)

    def list_elastic_ips(self, zone, **kwargs):
        """
        List Elastic IPs.

        Parameters:
            zone (Zone): the zone to list in
            
        Yields:
            ElasticIP: the next Elastic IP
        """

        try:
            _list = self.cs.listPublicIpAddresses(
                fetch_list=True, zoneid=zone.id, iselastic=True, **kwargs
            )

            for i in _list:
                yield ElasticIP._from_cs(self, i, zone=zone)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def get_elastic_ip(self, zone, address=None, id=None):
        """
        Retrieve an Elastic IP.

        Parameters:
            zone (Zone): the zone to retrieve from
            address (str): an Elastic IP address
            id (str): an Elastic IP identifier

        Returns:
            ElasticIP: an Elastic IP
        """

        if id is None and address is None:
            raise ValueError("either id or address must be specifed")

        try:
            elastic_ips = list(self.list_elastic_ips(zone, id=id, ipaddress=address))
        except APIException as e:
            if "does not exist" in e.error["errortext"]:
                raise ResourceNotFoundError
            raise

        if len(elastic_ips) == 0:
            raise ResourceNotFoundError

        return elastic_ips[0]

    ### Instance

    def create_instance(
        self,
        name,
        zone,
        type,
        template,
        volume_size=10,
        security_groups=None,
        anti_affinity_groups=None,
        private_networks=None,
        enable_ipv6=False,
        ssh_key=None,
        user_data=None,
    ):
        """
        Create a Compute instance.

        Parameters:
            name (str): the name of the instance
            zone (Zone): the zone in which to create the Compute instance
            type (InstanceType): the instance type
            template (InstanceTemplate): the instance template
            volume_size (int): the instance storage volume size in GB
            security_groups ([SecurityGroup]): a list of Security Groups to attach
                the instance to
            anti_affinity_groups ([AntiAffinityGroup]): a list of Anti-Affinity Groups
                to place the instance into
            private_networks ([PrivateNetwork]): a list of Private Networks to attach
                the instance to
            enable_ipv6 (bool): a flag indicating whether to enable IPv6 on the public
                network interface
            ssh_key (SSHKey): a SSH Key to deploy on the instance
            user_data (str): a cloud-init user data configuration

        Returns:
            Instance: the Compute instance created
        """

        try:
            res = self.cs.deployVirtualMachine(
                name=name,
                displayname=name,
                zoneid=zone.id,
                serviceofferingid=type.id,
                templateid=template.id,
                rootdisksize=volume_size,
                securitygroupids=list(i.id for i in security_groups)
                if security_groups
                else None,
                affinitygroupids=list(i.id for i in anti_affinity_groups)
                if anti_affinity_groups
                else None,
                networkids=list(i.id for i in private_networks)
                if private_networks
                else None,
                ip6=enable_ipv6,
                keypair=ssh_key.name if ssh_key else None,
                userdata=b64encode(bytes(user_data, encoding="utf-8"))
                if user_data
                else None,
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return Instance._from_cs(self, res["virtualmachine"], zone=zone)

    def list_instances(self, zone, name=None, ids=None, **kwargs):
        """
        List Compute instances.

        Parameters:
            zone (Zone): the zone to list in
            name (str): an Instance name to restrict results to
            ids ([str]): a list of Instance IDs to restrict results to

        Yields:
            Instance: the next Compute instance
        """

        try:
            _list = self.cs.listVirtualMachines(
                fetch_list=True, zoneid=zone.id, ids=ids, name=name, **kwargs
            )

            for i in _list:
                yield Instance._from_cs(self, i, zone=zone)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def get_instance(self, zone, id=None, ip_address=None):
        """
        Get a Compute instance.

        Parameters:
            zone (Zone): the zone to retrieve from
            id (str): an instance identifier
            ip_address (str): an instance IP address

        Returns:
            Instance: a Compute instance

        Note:
            The ``ip_address`` parameter is a Compute instance's *primary* IP address,
            not an Elastic IP.
        """

        if id is None and ip_address is None:
            raise ValueError("either id or ip_address must be specifed")

        try:
            instances = list(self.list_instances(zone, id=id, ipaddress=ip_address))
        except APIException as e:
            if "does not exist" in e.error["errortext"]:
                raise ResourceNotFoundError
            raise

        if len(instances) == 0:
            raise ResourceNotFoundError

        return instances[0]

    ### Instance Template

    def register_instance_template(
        self,
        name,
        url,
        checksum,
        zone,
        description=None,
        username=None,
        disable_ssh_key=False,
        disable_password_reset=False,
    ):
        """
        Register a custom instance template.

        Attributes:
            name (str): the instance template name
            description (str): an instance template description
            url (str): the URL at which to find the instance template disk image
            checksum (str): the instance template disk image MD5 checksum
            username (str): an username to log into Compute instances using this
                template
            disable_ssh_key (bool): a flag indicating whether to disable SSH key
                installation during Compute instance creation
            disable_password_reset (bool): a flag indicating whether to disable
                Compute instance password reset
        """
        return InstanceTemplate._register(
            compute=self,
            name=name,
            description=description,
            url=url,
            checksum=checksum,
            zone=zone,
            username=username,
            disable_ssh_key=disable_ssh_key,
            disable_password_reset=disable_password_reset,
        )

    def list_instance_templates(self, zone, name=None, type="exoscale", **kwargs):
        """
        List instance templates.

        Parameters:
            zone (Zone): the zone to list in
            name (str): an instance template name to restrict results to
            type (str): an instance template type to restrict results to

        Yields:
            InstanceTemplate: the next instance template
        """

        template_filters = {"exoscale": "featured", "mine": "self"}
        if type not in template_filters:
            raise ValueError(
                'invalid type "{}", supported types are: {}'.format(
                    type, ", ".join(template_filters)
                )
            )

        try:
            _list = self.cs.listTemplates(
                fetch_list=True,
                zoneid=zone.id,
                name=name,
                templatefilter=template_filters[type],
                **kwargs,
            )

            for i in _list:
                yield InstanceTemplate._from_cs(self, i, zone=zone)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def get_instance_template(self, zone, id):
        """
        Get an instance template.

        Parameters:
            zone (Zone): the zone to retrieve from
            id (str): an instance template identifier

        Returns:
            InstanceTemplate: an instance template
        """

        try:
            instance_templates = list(self.list_instance_templates(zone, id=id))
        except APIException as e:
            if "does not exist" in e.error["errortext"]:
                raise ResourceNotFoundError
            raise

        if len(instance_templates) == 0:
            raise ResourceNotFoundError

        return instance_templates[0]

    ### Instance Type

    def list_instance_types(self, **kwargs):
        """
        List Compute instance types.

        Yields:
            InstanceType: the next instance type
        """

        try:
            _list = self.cs.listServiceOfferings(fetch_list=True, **kwargs)

            for i in _list:
                yield InstanceType._from_cs(i)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def get_instance_type(self, name=None, id=None):
        """
        Get a Compute instance type.

        Parameters:
            name (str): an instance type name
            id (str): an instance type identifier

        Returns:
            InstanceType: a Compute instance type
        """

        if id is None and name is None:
            raise ValueError("either id or name must be specifed")

        try:
            instance_types = list(self.list_instance_types(id=id, name=name))
        except APIException as e:
            if "does not exist" in e.error["errortext"]:
                raise ResourceNotFoundError
            raise

        if len(instance_types) == 0:
            raise ResourceNotFoundError

        return instance_types[0]

    ### Instance Pool

    def create_instance_pool(
        self,
        zone,
        name,
        size,
        instance_type,
        instance_template,
        instance_volume_size=10,
        instance_security_groups=None,
        instance_private_networks=None,
        instance_enable_ipv6=False,
        instance_ssh_key=None,
        instance_user_data=None,
        description=None,
    ):
        """
        Create a Compute Instance Pool.

        Parameters:
            zone (Zone): the zone in which to create the Instance Pool
            name (str): the name of the Instance Pool
            description (str): a description of the Instance Pool
            size (int): the number of Compute instance members the pool must manage
            instance_type (InstanceType): the Compute instance members type
            instance_template (InstanceTemplate): the Compute instance template to use
                for members
            instance_volume_size (int): the Compute instance members storage volume
                size in GB
            instance_private_networks ([PrivateNetwork]): a list of Private Networks to
                attach the Compute instance members to
            instance_security_groups ([SecurityGroup]): a list of Security Groups to
                attach the Compute instance members to
            instance_enable_ipv6 (bool): a flag indicating whether to enable IPv6 on
                the Compute instance members public network interface
            instance_ssh_key (SSHKey): a SSH Key to deploy on the Compute instance
                members
            instance_user_data (str): a cloud-init user data configuration to apply to
                the Compute instance members

        Returns:
            InstancePool: the Compute Instance Pool created
        """

        if size <= 0:
            raise ValueError("size must be > 0")

        instance_security_group_ids = None
        if instance_security_groups:
            instance_security_group_ids = [i.id for i in instance_security_groups]

        instance_private_network_ids = None
        if instance_security_groups:
            instance_private_network_ids = [i.id for i in instance_private_networks]

        instance_ssh_key_name = None
        if instance_ssh_key:
            instance_ssh_key_name = instance_ssh_key.name

        instance_user_data_content = None
        if instance_user_data is not None:
            instance_user_data_content = b64encode(
                bytes(instance_user_data, encoding="utf-8")
            )

        try:
            res = self.cs.createInstancePool(
                name=name,
                description=description,
                size=size,
                zoneid=zone.id,
                serviceofferingid=instance_type.id,
                templateid=instance_template.id,
                rootdisksize=instance_volume_size,
                securitygroupids=instance_security_group_ids,
                networkids=instance_private_network_ids,
                ip6=instance_enable_ipv6,
                keypair=instance_ssh_key_name,
                userdata=instance_user_data_content,
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return InstancePool._from_cs(self, res)

    def list_instance_pools(self, zone, **kwargs):
        """
        List Compute Instance Pools.

        Parameters:
            zone (Zone): a zone to restrict results to

        Yields:
            InstancePool: the next Compute Instance Pool
        """

        try:
            _list = self.cs.listInstancePools(zoneid=zone.id, fetch_list=True, **kwargs)

            for i in _list:
                yield InstancePool._from_cs(self, i)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def get_instance_pool(self, id, zone):
        """
        Get an Instance Pool.

        Parameters:
            id (str): an Instance Pool identifier
            zone (Zone): the zone in which the Instance Pool is located in

        Returns:
            InstancePool: an Instance Pool
        """

        try:
            [res] = self.cs.getInstancePool(id=id, zoneid=zone.id, fetch_list=True)
        except CloudStackApiException as e:
            if "does not exist" in e.error["errortext"]:
                raise ResourceNotFoundError
            else:
                raise APIException(e.error["errortext"], e.error)

        return InstancePool._from_cs(self, res)

    ### Private Network

    def create_private_network(
        self, zone, name, description="", start_ip=None, end_ip=None, netmask=None
    ):
        """
        Create a Private Network.

        Parameters:
            zone (Zone): the zone in which to create the Private Network
            name (str): the Private Network name
            description (str): the Private Network description
            start_ip (str): the network IP range start address for managed
                Private Networks
            end_ip (str): the network IP range end address for managed
                Private Networks
            netmask (str): the network IP netmask for managed Private Networks

        Returns:
            PrivateNetwork: the Private Network created
        """

        try:
            res = self.cs.createNetwork(
                zoneid=zone.id,
                name=name,
                displaytext=description,
                startip=start_ip,
                endip=end_ip,
                netmask=netmask,
            )
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return PrivateNetwork._from_cs(self, res["network"], zone=zone)

    def list_private_networks(self, zone, **kwargs):
        """
        List Private Networks.

        Parameters:
            zone (Zone): the zone to list in

        Yields:
            PrivateNetwork: the next Private Network
        """

        try:
            _list = self.cs.listNetworks(fetch_list=True, zoneid=zone.id, **kwargs)

            for i in _list:
                yield PrivateNetwork._from_cs(self, i, zone=zone)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def get_private_network(self, zone, id):
        """
        Get a Private Network.

        Parameters:
            zone (Zone): the zone to retrieve from
            id (str): a Private Network identifier

        Returns:
            PrivateNetwork: a Private Network
        """

        try:
            private_networks = list(self.list_private_networks(zone, id=id))
        except APIException as e:
            if "does not exist" in e.error["errortext"]:
                raise ResourceNotFoundError
            raise

        if len(private_networks) == 0:
            raise ResourceNotFoundError

        return private_networks[0]

    ### Security Group

    def create_security_group(self, name, description=""):
        """
        Create a Security Group.

        Parameters:
            name (str): the Security group name
            description (str): the Security Group description

        Returns:
            SecurityGroup: the Security Group created
        """

        try:
            res = self.cs.createSecurityGroup(name=name, description=description)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return SecurityGroup._from_cs(self, res["securitygroup"])

    def list_security_groups(self, **kwargs):
        """
        List Security Groups.

        Yields:
            SecurityGroup: the next Security Group
        """

        try:
            _list = self.cs.listSecurityGroups(fetch_list=True, **kwargs)

            for i in _list:
                yield SecurityGroup._from_cs(self, i)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def get_security_group(self, name=None, id=None):
        """
        Get a Security Group.

        Parameters:
            name (str): a Security Group name 
            id (str): a Security Group identifier

        Returns:
            SecurityGroup: a Security Group
        """

        if id is None and name is None:
            raise ValueError("either id or name must be specifed")

        try:
            security_groups = list(
                self.list_security_groups(id=id, securitygroupname=name)
            )
        except APIException as e:
            if "does not exist" in e.error["errortext"]:
                raise ResourceNotFoundError
            raise

        if len(security_groups) == 0:
            raise ResourceNotFoundError

        return security_groups[0]

    ### SSH Key

    def create_ssh_key(self, name):
        """
        Create an SSH key.

        Parameters:
            name (str): the SSH key unique name

        Returns:
            SSHKey: the SSH key created
        """

        try:
            res = self.cs.createSSHKeyPair(name=name)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return SSHKey._from_cs(self, res["keypair"])

    def register_ssh_key(self, name, public_key):
        """
        Register an existing SSH key.

        Parameters:
            name (str): the SSH Key unique name
            public_key (str): the SSH public key to register
        
        Returns:
            SSHKey: the SSH key created
        """

        try:
            res = self.cs.registerSSHKeyPair(name=name, publickey=public_key)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return SSHKey._from_cs(self, res["keypair"])

    def list_ssh_keys(self, **kwargs):
        """
        List SSH keys.

        Yields:
            SSHKey: the next SSH key
        """

        try:
            _list = self.cs.listSSHKeyPairs(fetch_list=True, **kwargs)

            for i in _list:
                yield SSHKey._from_cs(self, i)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def get_ssh_key(self, name):
        """
        Get an SSH Key.

        Parameters:
            name (str): an SSH Key name 

        Returns:
            SSHKey: an SSH Key
        """

        try:
            ssh_keys = list(self.list_ssh_keys(name=name))
        except APIException as e:
            if "does not exist" in e.error["errortext"]:
                raise ResourceNotFoundError
            raise

        if len(ssh_keys) == 0:
            raise ResourceNotFoundError

        return ssh_keys[0]

    ### Zone

    def list_zones(self, **kwargs):
        """
        List zones.

        Yields:
            Zone: the next zone
        """

        try:
            _list = self.cs.listZones(fetch_list=True, **kwargs)

            for i in _list:
                yield Zone._from_cs(i)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

    def get_zone(self, name=None, id=None):
        """
        Get a zone.

        Parameters:
            name (str): a zone name
            id (str): a zone identifier

        Returns:
            Zone: a zone
        """

        if id is None and name is None:
            raise ValueError("either id or name must be specifed")

        try:
            zones = list(self.list_zones(id=id, name=name))
        except APIException as e:
            if "does not exist" in e.error["errortext"]:
                raise ResourceNotFoundError
            raise

        if len(zones) == 0:
            raise ResourceNotFoundError

        return zones[0]
