# Usage

Here are some practical library usage examples.

## Compute API

```python
import exoscale

exo = exoscale.Exoscale()

zone_gva2 = exo.compute.get_zone("ch-gva-2")

security_group_web = exo.compute.create_security_group("web")
for rule in [
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="HTTP",
        network_cidr="0.0.0.0/0",
        port="80",
        protocol="tcp",
    ),
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="HTTPS",
        network_cidr="0.0.0.0/0",
        port="443",
        protocol="tcp",
    ),
]:
    security_group_web.add_rule(rule)

elastic_ip = exo.compute.create_elastic_ip(zone_gva2)

instance = exo.compute.create_instance(
    name="web1",
    zone=zone_gva2,
    type=exo.compute.get_instance_type("medium"),
    template=list(
        exo.compute.list_instance_templates(
            zone_gva2,
            "Linux Ubuntu 18.04 LTS 64-bit")[0],
    root_disk_size=50,
    security_groups=[security_group_web],
    user_data="""#cloud-config
package_upgrade: true
packages:
- nginx
- php7.2-fpm
write_files:
- path: /etc/netplan/51-eip.yaml
  content: |
    network:
      version: 2
      renderer: networkd
      ethernets:
        lo:
          match:
            name: lo
          addresses:
            - {eip}/32
""".format(eip=elastic_ip.address)
)

instance.attach_elastic_ip(elastic_ip)

for instance in exo.compute.list_instances():
    print("{name} {zone} {ip}".format(
        name=instance.name,
        zone=instance.zone.name,
        ip=instance.ipv4_address,
    ))

# ...

instance.delete()
elastic_ip.delete()
security_group.delete()
```

## DNS API

```python
import exoscale

domain = exo.dns.create_domain(name="unicorns.net")
domain.add_record("srv1", "A", "1.2.3.4")
domain.add_record("www", "CNAME", "srv1.{}.".format(domain.name))

for rec in (r for r in domain.records if r.type not in {"SOA", "NS"}):
    print(rec.name, rec.type, rec.content)
```

## Storage API

```python
import exoscale
import pathlib
from datetime import datetime, timedelta

exo = exoscale.Exoscale()

backups_bucket = exo.storage.create_bucket("backups", zone="ch-gva-2")

backups = pathlib.Path("/tmp/backups")
for f in backups.iterdir():
    backups_bucket.put_file(str(f))

today = datetime.today()
for f in backups_bucket.list_files():
    if today - f.last_modification_date.replace(tzinfo=None) > timedelta(days=365):
        f.delete()
```

## Runstatus API

```python
import exoscale

exo = exoscale.Exoscale()

page = exo.runstatus.create_page("unicorns-net")
page.update(title="Unicorns Networks", custom_domain="status.unicorns.net")

exo.dns.get_domain(name="unicorns.net").
    add_record(name="status", type="CNAME", content="unicorns-net.runstat.us.")

page.add_service("Candy")
page.add_service("Rainbows")
page.add_service("Magic")

# ...

print("Services:")
for s in page.services:
    print("{}: {}".format(s.name, s.state))

print("Ongoing Incidents:")
for i in page.incidents:
    if i.end_date is None:
        print("[{}] {}".format(i.start_date, i.title))
```
