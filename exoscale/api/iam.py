# -*- coding: utf-8 -*-

"""
This submodule represents the Exoscale IAM API.
"""

import attr
from . import API, Resource, APIException, ResourceNotFoundError
from cs import CloudStack, CloudStackApiException

@attr.s
class APIKey(Resource):
    """
    An API key.

    Attributes:
        name (str): the API key display name
        key (str): the API key
        type (str): the API key type
        secret (str): the API key secret
        operations ([str]): the API key operations
    """

    iam = attr.ib(repr=False)
    res = attr.ib(repr=False)
    name = attr.ib()
    key = attr.ib()
    type = attr.ib()
    secret = attr.ib(repr=False)
    operations = attr.ib(repr=False)
    

    @classmethod
    def _from_cs(cls, iam, res):
        return cls(
            iam,
            res,
            name=res["name"],
            key=res["key"],
            type=res["type"],
            secret=res.get("secret", None),
            operations=res.get("operations", None),
        )

    def revoke(self):
        """
        Revoke the API key.

        Returns:
            None
        """

        try:
            self.iam.cs.revokeApiKey(key=self.key)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        self.res = None
        self.name = None
        self.key = None
        self.secret = None
        self.operations = None
        self.type = None


class IamAPI(API):
    """
    An Exoscale IAM API client.

    Parameters:
        key (str): the IAM API key
        secret (str): the IAM API secret
        endpoint (str): the IAM API endpoint
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
        return "IamAPI(endpoint='{}' key='{}')".format(self.endpoint, self.key)

    def __str__(self):
        return self.__repr__()

    ### API key

    def create_api_key(self, name, operations=None):
        """
        Create an API key.

        Parameters:
            name (str): the API key name
            operations (str): the API key description

        Returns:
           APIKey: the API key created
        """
        
        try:
            res = self.cs.createApiKey(name=name, operations=operations)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)

        return APIKey._from_cs(self, res["apikey"])

    def list_api_keys(self, **kwargs):
        """
        list API keys.

        Yields:
           APIKey: the next API key
        """

        try:
            _list = self.cs.listApiKeys(fetch_list=True, **kwargs)

            for i in _list:
                yield APIKey._from_cs(self, i)
        except CloudStackApiException as e:
            raise APIException(e.error["errortext"], e.error)