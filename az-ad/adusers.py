#!/usr/bin/env python3

import argparse
import json

import azure


def main(json_file, group):
    with open(json_file) as json_stream:
        active_user_data = json.load(json_stream)

    for user in active_user_data:
        azure_user = azure.find_user_by_email(user['emailAddress'])

        if azure_user:
            azure.add_group_member(group, azure_user['object_id'])
            print("User: {name} now in group".format(name=user['name']))
        else:
            print("User: {name} not found in Azure".format(name=user['name']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="Export of active users in JIRA", required=True)
    parser.add_argument("--group", help="The group to add users to", required=True)
    args = parser.parse_args()
    main(args.json, args.group)
