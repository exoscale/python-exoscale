import json
from itertools import chain
from pathlib import Path

from exoscale_auth import ExoscaleV2Auth

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


def _get_ref(path):
    root, *parts = path.split("/")
    if root != "#":
        raise AssertionError("Non-root path start", root, path)

    payload = API_SPEC
    while parts:
        item, *parts = parts
        payload = payload[item]

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
    def __init__(self, key, secret, url=None, **kwargs):
        for server in API_SPEC["servers"]:
            if server["url"] == url:
                break
        else:
            server = API_SPEC["servers"][0]
        variables = {
            var_name: var["default"]
            for var_name, var in server["variables"].items()
        }
        for k, v in kwargs.items():
            if k not in server["variables"]:
                raise TypeError(f"Unhandled keyword argument {k!r}.")
            variables[k] = v

        self.endpoint = server["url"].format(**variables)

        session = requests.Session()
        session.auth = ExoscaleV2Auth(key, secret)
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
        if parameters is None:
            parameters = {}
        for param in op["operation"].get("parameters", []):
            name = param["name"]
            if param["required"] and name not in parameters:
                raise ValueError(f"Missing mandatory param {name!r}")
            if name in parameters:
                value = parameters[name]
                if param["in"] == "path":
                    # TODO validate
                    path = path.format(**{name: value})
                elif param["in"] == "query":
                    query_params[name] = value

        url = f"{self.endpoint}{path}"

        json = {}
        if body is not None:
            # TODO validate
            json["json"] = body

        response = self.session.request(
            method=op["verb"].upper(), url=url, params=query_params, **json
        )
        return response.json()


_type_translations = {
    "string": "str",
    "integer": "int",
    "object": "dict",
    "array": "list",
    "boolean": "bool",
}


def _return_docstring(operation):
    [status_code] = operation["responses"].keys()
    [ctype] = operation["responses"][status_code]["content"].keys()
    return_schema = operation["responses"][status_code]["content"][ctype][
        "schema"
    ]
    if "$ref" in return_schema:
        ref = _get_ref(return_schema["$ref"])
        if "description" in ref:
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

        url (str): Endpoint URL template to use. Must be one of ``{servers}``.
            Defaults to ``{default_server!r}``.

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
