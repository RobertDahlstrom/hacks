#!/usr/bin/env python3

import argparse
import json

import azure_wrapper


def main(json_file, group):
    with open(json_file) as json_stream:
        active_user_data = json.load(json_stream)

    count = 0
    for user in active_user_data:
        email = user['emailAddress']
        azure_user = azure_wrapper.find_user_by_email(email)

        if azure_user:
            azure_wrapper.add_group_member(group, azure_user['objectId'])
            print("User: {email} now in group".format(email=email))
        else:
            print("User: {email} not found in Azure".format(email=email))
        count += 1

    print("{count} users processed".format(count=count))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="List of json objects containing emailAddress", required=True)
    parser.add_argument("--group", help="The group to add users to", required=True)
    args = parser.parse_args()
    main(args.json, args.group)
