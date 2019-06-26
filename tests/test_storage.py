#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from exoscale.api.storage import *
from .conftest import _random_str


class TestStorage:
    ### Bucket

    def test_create_bucket(self, exo, test_prefix):
        bucket_name = "-".join([test_prefix, _random_str()])

        bucket = exo.storage.create_bucket(name=bucket_name)
        assert bucket.name == bucket_name

        exo.storage.boto.delete_bucket(Bucket=bucket_name)

    def test_list_buckets(self, exo, bucket):
        bucket = bucket()

        buckets = list(exo.storage.list_buckets())
        # We cannot guarantee that there will be only our resources,
        # so we ensure we get at least our fixture bucket
        assert len(buckets) >= 1

    def test_get_bucket(self, exo, bucket):
        bucket1 = Bucket(exo.storage, {}, bucket())

        bucket = exo.storage.get_bucket(name=bucket1.name)
        assert bucket.name == bucket1.name

        with pytest.raises(ResourceNotFoundError) as excinfo:
            bucket = exo.storage.get_bucket(name="lolnope")
            assert bucket is None
        assert excinfo.type == ResourceNotFoundError
