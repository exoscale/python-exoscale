import copy
from itertools import chain

import requests

from .exceptions import (
    ExoscaleAPIAuthException,
    ExoscaleAPIClientException,
    ExoscaleAPIServerException,
)


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


def _get_ref(api_spec, path):
    root, *parts = path.split("/")
    if root != "#":
        raise AssertionError("Non-root path start", root, path)

    # We're going to mutate payload later on, so make a full copy to avoid
    # altering api_spec.
    payload = copy.deepcopy(_get_in(api_spec, parts))

    for name, desc in payload.get("properties", {}).items():
        if "$ref" in desc:
            resolved_schema = _get_ref(api_spec, desc["$ref"])
            for k, v in desc.items():
                if k != "$ref":
                    resolved_schema[k] = v
            payload["properties"][name] = resolved_schema
    payload["$schema"] = "http://json-schema.org/draft-04/schema"
    return payload


_type_translations = {
    "string": "str",
    "integer": "int",
    "object": "dict",
    "array": "list",
    "boolean": "bool",
    "number": "float",
}


def _status_code_docstring(api_spec, operation, status_code):
    [ctype] = operation["responses"][status_code]["content"].keys()
    return_schema = operation["responses"][status_code]["content"][ctype][
        "schema"
    ]
    if "$ref" in return_schema:
        ref = _get_ref(api_spec, return_schema["$ref"])
        if (
            "properties" in ref
            and ref["type"] == "object"
            and "description" in ref
        ):
            body = {}
            for name, prop in ref["properties"].items():
                if "$ref" in prop:
                    _ref = _get_ref(api_spec, prop["$ref"])
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
            doc = f"{_type_translations[ref['type']]}: {ref['description']}."
        else:
            doc = _type_translations[ref["type"]]
    else:
        doc = _type_translations[return_schema["type"]]
    return doc


def _return_docstring(api_spec, operation):
    status_codes_docs = [
        "{status_code}: {ret_type}".format(
            status_code=status_code,
            ret_type=_status_code_docstring(api_spec, operation, status_code),
        )
        for status_code in operation["responses"].keys()
    ]

    return "\n        ".join(status_codes_docs)

class BaseClient:
    _api_spec = None
    _by_operation = None

    def __init__(self, url=None, **kwargs):
        if url is None:
            server = self._api_spec["servers"][0]
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

        self.http_client = requests.Session()

    def __repr__(self):
        return f"<Client endpoint={self.endpoint}>"

    def _call_operation(self, operation_id, parameters=None, body=None):
        op = self._by_operation[operation_id]

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

        response = self.http_client.request(
            method=op["verb"].upper(), url=url, params=query_params, **json
        )

        # Error handling
        if response.status_code == 403:
            raise ExoscaleAPIAuthException(
                f"Authentication error {response.status_code}: {response.text}",
                response,
            )
        if 400 <= response.status_code < 500:
            raise ExoscaleAPIClientException(
                f"Client error {response.status_code}: {response.text}",
                response,
            )
        elif response.status_code >= 500:
            raise ExoscaleAPIServerException(
                f"Server error {response.status_code}: {response.text}",
                response,
            )

        return response.json()


def _args_docstring(parameters, body):
    return "\n\n        ".join(chain(parameters.values(), body.values()))


def _create_operation_call(
    py_operation_name, operation_name, operation, api_spec
):
    docstring = """{summary}

    Args:
        {args}

    Returns:
        {ret}
    """

    parameters = {}
    body = {}
    normalized_names = {}
    for param in operation.get("parameters", []):
        name = param["name"]
        if "$ref" in param["schema"]:
            ref = _get_ref(api_spec, param["schema"]["$ref"])
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
            ref = _get_ref(api_spec, schema["$ref"])
            properties = ref["properties"]
        else:
            properties = schema["properties"]

        for name, prop in properties.items():
            if "$ref" in prop:
                ref = _get_ref(api_spec, prop["$ref"])
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
            if k not in normalized_names:
                raise TypeError(f"Unhandled keyword argument {k!r}.")
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
        ret=_return_docstring(api_spec, operation),
    )
    return _api_call


def _client_docstring(api_spec):
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
    for server in api_spec["servers"]:
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


def create_client_class(api_spec):
    by_operation = {}
    for path, item in api_spec["paths"].items():
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
            by_operation[operation["operationId"]] = {
                "verb": verb,
                "path": path,
                "operation": operation,
            }

    class_name = "Client"
    bases = [BaseClient]
    class_attributes = {
        "_api_spec": api_spec,
        "_by_operation": by_operation,
        "__doc__": _client_docstring(api_spec),
    }

    for operation_name, operation in by_operation.items():
        py_operation_name = operation_name.replace("-", "_")
        op_fn = _create_operation_call(
            py_operation_name,
            operation_name,
            operation["operation"],
            api_spec,
        )

        class_attributes[py_operation_name] = op_fn

    cls = type(class_name, tuple(bases), class_attributes)
    return cls
