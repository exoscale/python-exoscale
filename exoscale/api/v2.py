"""

``exoscale.api.v2`` provides a low-level client targeting Exoscale's
OpenAPI-based V2 API. This client is dynamically generated from the OpenAPI
definition shipped with the package.

Examples:
    Creating a client targeting one of the available zones:

    >>> from exoscale.api.v2 import Client
    >>> c = Client("api-key", "api-secret", zone="de-fra-1")
    >>> c.list_instances()
    {'instances': []}

    Creating a client targeting an endpoint specifically:

    >>> from exoscale.api.v2 import Client
    >>> c = Client("api-key", "api-secret", url="https://api-ch-gva-2.exoscale.com/v2")
    >>> c.list_instances()
    {'instances': []}

"""

import copy
import json
import time
from itertools import chain
from pathlib import Path

from exoscale_auth import ExoscaleV2Auth
from .exceptions import (
    ExoscaleAPIException,
    ExoscaleAPIClientException,
    ExoscaleAPIServerException,
    ExoscaleAPIAuthException,
)


import requests

with open(Path(__file__).parent.parent / "openapi.json", "r") as f:
    API_SPEC = json.load(f)

BY_OPERATION = {}
for path, item in API_SPEC["paths"].items():
    for verb, operation in item.items():
        if verb not in {
            "get",
            "put",
            "post",
            "delete",
            "head",
            "options",
            "patch",
            "trace",
        }:
            raise AssertionError(
                "Unhandled path item object (https://swagger.io/specification/#pathItemObject) field",  # noqa
                verb,
            )
        BY_OPERATION[operation["operationId"]] = {
            "verb": verb,
            "path": path,
            "operation": operation,
        }


def _get_in(payload, keys):
    """
    Returns the value in a nested dict, where items is a sequence of keys.
    """
    k, *ks = keys
    ret = payload[k]
    if ks:
        return _get_in(ret, ks)
    else:
        return ret


def _get_ref(path):
    root, *parts = path.split("/")
    if root != "#":
        raise AssertionError("Non-root path start", root, path)

    # We're going to mutate payload later on, so make a full copy to avoid
    # altering API_SPEC.
    payload = copy.deepcopy(_get_in(API_SPEC, parts))

    for name, desc in payload.get("properties", {}).items():
        if "$ref" in desc:
            resolved_schema = _get_ref(desc["$ref"])
            for k, v in desc.items():
                if k != "$ref":
                    resolved_schema[k] = v
            payload["properties"][name] = resolved_schema
    payload["$schema"] = "http://json-schema.org/draft-04/schema"
    return payload


class BaseClient:
    def __init__(self, key, secret, url: str | None = None, polling_interval: int = 5, **kwargs):
        if url is None:
            server = API_SPEC["servers"][0]
            variables = {
                var_name: var["default"]
                for var_name, var in server["variables"].items()
            }
            for k, v in kwargs.items():
                if k not in server["variables"]:
                    raise TypeError(f"Unhandled keyword argument {k!r}.")
                if choices := server["variables"][k].get("enum"):
                    if v not in choices:
                        choices_repr = "', '".join(choices)
                        raise TypeError(
                            f"Invalid {k}: must be one of '{choices_repr}'."
                        )
                variables[k] = v

            self.endpoint = server["url"].format(**variables)
        else:
            self.endpoint = url

        session = requests.Session()
        session.auth = ExoscaleV2Auth(key, secret)
        self.polling_interval = polling_interval
        self.session = session
        self.key = key

    def __repr__(self):
        return (
            f"<Client endpoint={self.endpoint}"
            f" key={self.key} secret=***masked***>"
        )

    def _call_operation(self, operation_id, parameters=None, body=None):
        op = BY_OPERATION[operation_id]

        path = op["path"]
        query_params = {}
        path_params = {}
        if parameters is None:
            parameters = {}
        for param in op["operation"].get("parameters", []):
            name = param["name"]
            if param["required"] and name not in parameters:
                raise ValueError(f"Missing mandatory param {name!r}")
            if name in parameters:
                value = parameters[name]
                if param["in"] == "path":
                    path_params[name] = value
                elif param["in"] == "query":
                    query_params[name] = value

        path = path.format(**path_params)

        url = f"{self.endpoint}{path}"

        json = {}
        if body is not None:
            # TODO validate
            json["json"] = body

        response = self.session.request(
            method=op["verb"].upper(), url=url, params=query_params, **json
        )

        # Error handling
        if response.status_code == 403:
            raise ExoscaleAPIAuthException(
                f"Authentication error {response.status_code}: {response.text}"
            )
        if 400 <= response.status_code < 500:
            raise ExoscaleAPIClientException(
                f"Client error {response.status_code}: {response.text}"
            )
        elif response.status_code >= 500:
            raise ExoscaleAPIServerException(
                f"Server error {response.status_code}: {response.text}"
            )

        return response.json()

    def wait(self, operation_id: str, states: list[str] = None, timeout: int = None):
        """Wait is a helper that waits for async operation to reach the final state.
            Final states are one of: failure, success, timeout.
            If states argument are given, returns an error if the final state not match on of those.

            Args:
                * operation_id (str)

                * states (list(str)): desired operation status. Values are ``'failure'``, ``'success'``, ``'timeout'``.

                * timeout (int): Client timeout to wait for the operation to finish (in seconds).

            Returns:
                dict: Operation. A dictionnary with the following keys:

                  * **id** (str): Operation ID.

                  * **reason** (str): Operation failure reason. Values are ``'busy'``, ``'conflict'``, ``'fault'``, ``'forbidden'``, ``'incorrect'``, ``'interrupted'``, ``'not-found'``, ``'partial'``, ``'unavailable'``, ``'unknown'``, ``'unsupported'``.

                  * **reference** (dict): Related resource reference.

                  * **message** (str): Operation message.

                  * **state** (str): Operation status. Values are ``'failure'``, ``'pending'``, ``'success'``, ``'timeout'``.

            Raises:
                * ExoscaleAPIException: The final state doesn't match the desired state.

                * TimeoutError: If a timeout is specified, thrown if the operation is still in progress after reaching the timeout.
        """

        if operation_id is None:
            raise ValueError("operation_id is None")

        start_time = time.time()

        while True:
            # Check for timeout
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Operation {operation_id} timed out")

            # Fetch the latest operation state
            operation = self.get_operation(id=operation_id)

            if operation["state"] != "pending":
                # Operation has reached a final state
                if not states or operation["state"] in states:
                    return operation  # Success: return the operation
                else:
                    # Error: final state does not match expected states
                    ref = operation.get("reference", {})
                    raise ExoscaleAPIException(
                        f"Operation: '{operation_id}' {ref}, "
                        f"state: {operation['state']}, reason: '{operation.get('reason', '')}', "
                        f"message: '{operation.get('message', '')}'"
                    )

            # Operation is still pending, wait and retry
            time.sleep(self.polling_interval)

_type_translations = {
    "string": "str",
    "integer": "int",
    "object": "dict",
    "array": "list",
    "boolean": "bool",
    "number": "float",
}


def _return_docstring(operation):
    [status_code] = operation["responses"].keys()
    [ctype] = operation["responses"][status_code]["content"].keys()
    return_schema = operation["responses"][status_code]["content"][ctype][
        "schema"
    ]
    if "$ref" in return_schema:
        ref = _get_ref(return_schema["$ref"])
        if (
            "properties" in ref
            and ref["type"] == "object"
            and "description" in ref
        ):
            body = {}
            for name, prop in ref["properties"].items():
                if "$ref" in prop:
                    _ref = _get_ref(prop["$ref"])
                    item = _ref
                else:
                    item = prop
                typ = _type_translations[item["type"]]
                desc = prop.get("description")
                if "enum" in item:
                    choices = "``, ``".join(map(repr, item["enum"]))
                    desc += f". Values are ``{choices}``"
                suffix = f": {desc}" if desc else ""
                normalized_name = name.replace("-", "_")
                body[normalized_name] = (
                    f"**{normalized_name}** ({typ}){suffix}."
                )

            doc = (
                f"dict: {ref['description']}. A dictionnary with the following keys:"
                + "\n\n          * ".join([""] + list(body.values()))
            )
        elif "description" in ref:
            doc = f'{_type_translations[ref["type"]]}: {ref["description"]}.'
        else:
            doc = _type_translations[ref["type"]]
    else:
        doc = _type_translations[return_schema["type"]]
    return doc


def _args_docstring(parameters, body):
    return "\n\n        ".join(chain(parameters.values(), body.values()))


def _create_operation_call(py_operation_name, operation_name, operation):
    docstring = """{summary}

    Args:
        {args}

    Returns:
        {ret}
    """

    parameters = {}
    body = {}
    normalized_names = {}
    for param in operation["parameters"]:
        name = param["name"]
        if "$ref" in param["schema"]:
            ref = _get_ref(param["schema"]["$ref"])
            typ = _type_translations[ref["type"]]
        else:
            typ = _type_translations[param["schema"]["type"]]
        normalized_name = name.replace("-", "_")
        normalized_names[normalized_name] = name
        parameters[normalized_name] = f"{normalized_name} ({typ})."

    if "requestBody" in operation:
        schema = operation["requestBody"]["content"]["application/json"][
            "schema"
        ]
        if "$ref" in schema:
            ref = _get_ref(schema["$ref"])
            properties = ref["properties"]
        else:
            properties = schema["properties"]

        for name, prop in properties.items():
            if "$ref" in prop:
                ref = _get_ref(prop["$ref"])
                item = ref
            else:
                item = prop
            typ = _type_translations[item["type"]]
            desc = prop.get("description")
            if "enum" in item:
                choices = "``, ``".join(map(repr, item["enum"]))
                desc += f". Must be one of ``{choices}``"
            suffix = f": {desc}" if desc else ""
            normalized_name = name.replace("-", "_")
            normalized_names[normalized_name] = name
            body[normalized_name] = f"{normalized_name} ({typ}){suffix}."

    def _api_call(self, *args, **kwargs):
        if args:
            raise TypeError(
                f"{py_operation_name}() only accepts keyword arguments."
            )
        _params = {}
        _body = {}
        for k, v in kwargs.items():
            api_name = normalized_names[k]
            if k in parameters:
                _params[api_name] = v
            elif k in body:
                _body[api_name] = v
            else:
                raise TypeError(f"Unhandled keyword argument {k!r}.")

        if not _body:
            _body = None

        return self._call_operation(
            operation_name, parameters=_params, body=_body
        )

    _api_call.__name__ = py_operation_name
    _api_call.__qualname__ = f"Client.{py_operation_name}"
    _api_call.__doc__ = docstring.format(
        summary=operation["summary"],
        args=_args_docstring(parameters, body),
        ret=_return_docstring(operation),
    )
    return _api_call


def _client_docstring():
    template = """Create an API client.

    Args:
        key (str): Exoscale API key.

        secret (str): Exoscale API secret.

        url (str): Endpoint URL to use. Defaults to ``{default_server!r}``.

        {dynamic_args}

    Returns:
        Client: A configured API client.
    """
    servers = []
    args = {}
    for server in API_SPEC["servers"]:
        servers.append(server["url"])
        for name, variable in server["variables"].items():
            if name in args:
                continue
            choices = "``, ``".join(map(repr, variable["enum"]))
            typ = type(variable["default"]).__name__
            args[name] = (
                f"{name} ({typ}): one of ``{choices}``."
                f" Defaults to ``{variable['default']!r}``."
            )
    dynamic_args = "\n\n        ".join(args.values())
    return template.format(
        servers="``, ``".join(map(repr, servers)),
        default_server=servers[0],
        dynamic_args=dynamic_args,
    )


def _create_client_class():
    class_name = "Client"
    bases = [BaseClient]
    class_attributes = {"__doc__": _client_docstring()}
    for operation_name, operation in BY_OPERATION.items():
        py_operation_name = operation_name.replace("-", "_")
        class_attributes[py_operation_name] = _create_operation_call(
            py_operation_name, operation_name, operation["operation"]
        )
    cls = type(class_name, tuple(bases), class_attributes)
    return cls


Client = _create_client_class()
