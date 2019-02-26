#!/usr/bin/env python3
import argparse
import sys

import yaml
import base64
import json


def decode_secret_data(yaml_data):
    if 'data' not in yaml_data:
        print("No data section found in Yaml file, nothing to do")
        return

    print("data:")
    for key, encoded in yaml_data['data'].items():
        decoded = base64.b64decode(encoded).decode('utf-8')
        print("  {key}: ".format(key=key), end='')

        value = decoded
        try:
            json_object = json.loads(decoded)
            decoded = json.dumps(json_object, indent=2)
        except ValueError:
            pass
        print(value)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Decodes base64 encoded Yaml data structures. "
                    "E.g. kubectl get secret my-secret -o yaml | ./plain-secrets.py"
    )
    parser.add_argument("--yaml", help="The input yaml file to decode base64 encoded data section in")
    args = parser.parse_args()

    handle = sys.stdin
    if args.yaml is None:
        yaml_data = yaml.load(sys.stdin)
    else:
        with open(args.yaml) as stream:
            yaml_data = yaml.load(stream)

    decode_secret_data(yaml_data)
