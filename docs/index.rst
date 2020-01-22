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
