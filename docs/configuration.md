# [deprecated] Configuration

**This document refers to deprecated code paths that will be removed in future releases. It is advised to switch to the [V2 API bindings](v2.html).**

The python-exoscale library can be configured using class parameters, a
configuration file or environment variables.

## Class parameters

See the `Exoscale` [class documentation][exoclass] for configuration-related
parameters.

## Configuration file

The configuration file format is [TOML][toml], the expected structure is:

```toml
default_profile = "alice"

[[profiles]]
name = "alice"
api_key = "EXOa1b2c3..."
api_secret = "..."

[[profiles]]
name = "bob"
api_key = "EXOd5e6f7..."
api_secret = "..."
```

A `[[profiles]]` entry is a dictionary supporting the following key/values
(keys marked with a "*" are required):

* `name`*: the name of the profile
* `api_key`*: the profile Exoscale client API key
* `api_secret`*: the profile Exoscale client API secret
* `storage_zone`: an Exoscale Object Storage zone (required for using the
  Storage API)
* `compute_api_endpoint`: an alternative Exoscale Compute API endpoint
* `dns_api_endpoint`: an alternative Exoscale DNS API endpoint
* `storage_api_endpoint`: an alternative Exoscale Storage API endpoint
* `runstatus_api_endpoint`: an alternative Exoscale Runstatus API endpoint
* `iam_api_endpoint`: an alternative Exoscale IAM API endpoint

## Environment variables

The following environment variables can be used in place of a configuration
file:

* `EXOSCALE_API_KEY`: a Exoscale client API key
* `EXOSCALE_API_SECRET`: a Exoscale client API secret
* `EXOSCALE_COMPUTE_API_ENDPOINT`: an alternative Exoscale Compute API endpoint
* `EXOSCALE_DNS_API_ENDPOINT`: an alternative Exoscale DNS API endpoint
* `EXOSCALE_RUNSTATUS_API_ENDPOINT`: an alternative Exoscale Runstatus API
  endpoint
* `EXOSCALE_IAM_API_ENDPOINT`: an alternative Exoscale IAM API endpoint
* `EXOSCALE_STORAGE_API_ENDPOINT`: an alternative Exoscale Storage API endpoint
* `EXOSCALE_STORAGE_ZONE`: an Exoscale Storage zone
* `EXOSCALE_CONFIG_FILE`: an alternative configuration file location (default:
  `$HOME/.exoscale/config.toml`)

[toml]: https://github.com/toml-lang/toml
[exoclass]: /exoscale.html#exoscale.Exoscale
