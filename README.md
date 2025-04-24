# python-exoscale: Python bindings for Exoscale API

[![Actions Status](https://github.com/exoscale/python-exoscale/workflows/CI/badge.svg)](https://github.com/exoscale/python-exoscale/actions?query=workflow%3ACI)

This library allows developers to use the [Exoscale] cloud platform API with
extensive Python bindings. API documentation and usage examples can be found
at this address: https://exoscale.github.io/python-exoscale

## Development

Install [uv](https://docs.astral.sh/uv/) and run:

```
uv sync
```

You can then run pytest with the following command:

```
uv run pytest -x -s -vvv
```

[exoscale]: https://www.exoscale.com/

## Releasing

* Add changes to the changelog in `docs/changes.rst`
* Bump version in `exoscale/__init__.py`
* Commit and tag with `v{version}`
* Wait for the [package
  workflow](https://github.com/exoscale/python-exoscale/actions/workflows/pypi-package.yaml)
  to complete its first step
* Review the release artifacts and approve
