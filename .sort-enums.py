#!/usr/bin/env python
import json
import sys


def walk_map(payload):
    for key, value in payload.items():
        if key == "enum" and isinstance(value, list):
            payload[key] = list(sorted(value))
        elif isinstance(value, dict):
            walk_map(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    walk_map(item)


def sort_enums():
    payload = json.loads(sys.stdin.read())
    walk_map(payload)
    print(json.dumps(payload))


if __name__ == "__main__":
    sort_enums()
