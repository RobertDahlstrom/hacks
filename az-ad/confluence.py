#!/usr/bin/env python3

import argparse
import json
import requests


def filter_active_users(results):
    filtered = []
    for result in results:
        if result['status'] == 'current':
            result['emailAddress'] = result['username']
            filtered.append(result)
    return filtered


def main(args):
    # https://confluence.electrolux.io/rest/api/group/confluence-administrators/member?expand=status
    url = "https://{args.host}/rest/api/group/{args.group}/member?expand=status".format(args=args)
    request = requests.get(url, auth=(args.user, args.password))
    request.raise_for_status()

    active_users = filter_active_users(request.json()['results'])

    print(json.dumps(active_users, indent=4, separators=(',', ': ')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True)
    parser.add_argument('--user', default='admin')
    parser.add_argument('--password', required=True)
    parser.add_argument('--group', required=True)

    main(parser.parse_args())
