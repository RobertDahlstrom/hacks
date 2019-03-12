#!/usr/bin/env python3

import argparse
import json
import subprocess


def user_from_ad(user):
    # az ad user list --filter "mail eq 'robert.dahlstrom@diabol.se'"
    command = "az ad user list --filter \"mail eq '{mail}'\"".format(mail=user['emailAddress'])
    proc = subprocess.run(command, shell=True, capture_output=True, encoding='utf-8')
    json_data = json.loads(proc.stdout)

    if len(json_data) == 1:
        return json_data[0]

    return None


def user_in_group(azure_user, group):
    """
    json_data:
        [{displayName: ...,objectId: ...}]
    """
    command = "az ad user get-member-groups --upn-or-object-id {object_id}".format(object_id=azure_user['objectId'])
    proc = subprocess.run(command, shell=True, capture_output=True, encoding='utf-8')
    proc.check_returncode()
    json_data = json.loads(proc.stdout)
    for member_group in json_data:
        if member_group['displayName'] == group:
            return True

    return False


def add_user_to_group(azure_user, group):
    if user_in_group(azure_user, group):
        return

    command = "az ad group member add --group '{group}' --member-id {object_id}".format(
        group=group, object_id=azure_user['objectId']
    )
    proc = subprocess.run(command, shell=True, encoding='utf-8')
    proc.check_returncode()


def main(json_file, group):
    with open(json_file) as json_stream:
        active_user_data = json.load(json_stream)

    for user in active_user_data:
        azure_user = user_from_ad(user)

        if azure_user:
            add_user_to_group(azure_user, group)
            print("User: {name} now in group".format(name=user['name']))
        else:
            print("User: {name} not found in Azure".format(name=user['name']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="Export of active users in JIRA", required=True)
    parser.add_argument("--group", help="The group to add users to", required=True)
    args = parser.parse_args()
    main(args.json, args.group)
