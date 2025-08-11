Changelog
---------

0.13.0 (2025-08-11)
-------------------

* Support hr-zag-1 zone
* Remove DBaaS service Redis (replaced by Valkey)

0.12.0 (2025-06-04)
~~~~~~~~~~~~~~~~~~~

* Internals: abstract client generation logic into a separate
  ``exoscale.api.generator`` namespace.
* API changes and additions:

  * SKS: Rotate CCM credentials
  * Instance: TMP and Secure Boot support
  * DBaaS:

    * Kafka: cluster networking options
    * New zone option: ``hr-zag-1``

0.11.0 (2025-04-24)
~~~~~~~~~~~~~~~~~~~

* Bump python version requirement to 3.8 due to the use of the walrus
  operator.
* Add ``Client.wait(operation_id)`` to poll for the result of an asynchronous
  API operation.

0.10.0 (2024-05-29)
~~~~~~~~~~~~~~~~~~~

* Introduce exception classes that gets raised when the API responds with 4xx
  or 5xx HTTP statuses.

0.9.1 (2024-04-29)
~~~~~~~~~~~~~~~~~~

``exoscale.api.v2.Client`` improvements:

* Client initialization accepts two signatures: ``Client(key, secret, zone)`` for
  typical use and ``Client(key, secret, url)`` when needing to target another
  endpoint than the public endpoint template.
* Drop support for Python 3.7, add Python 3.12 to the testing matrix.
* Fix operations with multiple path parameters (`@thomas-chauvet https://github.com/exoscale/python-exoscale/pull/57`)
* API changes and additions:

  * DBaaS:

    * integrations settings
    * Split secrets over to separate endpoints
    * Add zone to service details
  * DNS record types cleanup
  * Instance password reset operation
  * Provide ``at-vie-2`` in the zones choices
  * Block Storage operations and CSI addon
  * Audit-trail format adjustments
  * Add MAC address to private network attachments

0.8.0 (2023-05-11)
~~~~~~~~~~~~~~~~~~

- Add ``exoscale.api.v2.Client``: a low-level API client targeting the Exoscale
  V2 API.

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
