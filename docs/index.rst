python-exoscale library documentation
=====================================

This library allows developpers to use the `Exoscale`_ cloud platform API
with high-level Python bindings.

.. _Exoscale: https://www.exoscale.com/

.. note::
   This library is compatible with Python 3.6+ only.

.. toctree::
  :maxdepth: 10

  configuration
  usage
  modules


Changelog
---------

0.7.1 (2021-10-18)
~~~~~~~~~~~~~~~~~~

Fixes
*****

- compute: fix `instance_private_networks` arg check in `create_instance_pool()` method


0.7.0 (2021-05-11)
~~~~~~~~~~~~~~~~~~

Features
********

- compute: add support for Deploy Targets resources
- compute: Instance Pools now support Elastic IP attachment, Instance Prefix and
- Deploy Targets
- compute: the ``InstancePool.update()`` method now supports updating Anti-Affinity
  Groups, IPv6 enabling, Security Groups, Private Networks and SSH Key.
- compute: new ``InstancePool.evict()`` method

Changes
*******

- compute: the ``get_instance_pool()`` method now accepts either of ``name``/``id``
  parameters
- compute: the ``InstancePool.delete()`` method ``wait``/``max_poll`` parameters have
  been removed


0.6.0 (2021-04-21)
~~~~~~~~~~~~~~~~~~

Features
********

- compute: the ``SecurityGroup.update()`` now updates the Compute instance Security
  Groups membership live without requiring to stop the instance
- compute: add ``Instance.user_data`` property
- compute: add ``InstanceTemplate.boot_mode`` attribute
- dns: ``create_dns_record()`` now returns the created record

Fixes
*****

- compute: don't crash when an Instance Template doesn't have details metadata


0.5.2 (2021-04-13)
~~~~~~~~~~~~~~~~~~

Fixes
*****

- compute: add missing `bootmode` parameter to `register_instance_template()` (#32)


0.5.1 (2021-03-16)
~~~~~~~~~~~~~~~~~~

Fixes
*****

- Exclude tests from Python packaging


0.5.0 (2021-03-15)
~~~~~~~~~~~~~~~~~~

Features
********

- compute: add Anti-Affinity Groups support to Instance Pools (#27)

Fixes
*****

- Rely on pathlib for home lookup (#29)
- compute: don't crash when listing instances generated from templates (#28)


0.4.0 (2020-12-07)
~~~~~~~~~~~~~~~~~~

Features
********

- compute: add support for Network Load Balancers
- compute: add support for Elastic IP HTTPS health checking
- compute: add support for snapshot exporting

Changes
*******

- compute: `get_instance_pool()` arguments order


0.3.0 (2020-01-22)
~~~~~~~~~~~~~~~~~~

New
***

- Add support for IAM (``iam`` submodule)

Features
********

- Allow HTTP session retry policy to be user configurable
- compute: add support for Instance Pools
- compute: add support for Elastic IP descriptions
- compute: add Instance ``creation_date`` attribute

Fixes
*****

- storage: fix failing integration tests
- storage: honor global client settings


0.2.0 (2019-10-09)
~~~~~~~~~~~~~~~~~~

Features
********

- storage: add Bucket/BucketFile ``url`` attribute

Fixes
*****

- compute: fix unhandled exception in ``get_*`` functions

Changes
*******

- compute: ``create_instance()`` function *root_disk_size* parameter has been renamed
  to *volume_size*
- compute: ``get_elastic_ip()`` function now requires a *zone* parameter
- compute: ``get_instance_template()`` function now requires a *zone* parameter
- compute: ``get_instance()`` function now requires a *zone* parameter
- compute: ``get_private_network()`` function now requires a *zone* parameter
- compute: ``list_elastic_ips()`` function now requires a *zone* parameter
- compute: ``list_instance_templates()`` function now requires a *zone* parameter
- compute: ``list_instances()`` function now requires a *zone* parameter
- compute: ``list_private_networks()`` function now requires a *zone* parameter


0.1.1 (2019-09-12)
~~~~~~~~~~~~~~~~~~

- Initial release
