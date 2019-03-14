#!/usr/bin/env python3

import argparse
import json
import requests


def main(args):
    # https://docs.atlassian.com/bitbucket-server/rest/6.1.1/bitbucket-rest.html
    url = 'https://{args.host}/rest/api/1.0/admin/users?limit=1000'.format(args=args)
    request = requests.get(url, auth=(args.user, args.password))
    request.raise_for_status()
    print(json.dumps(request.json()['values'], indent=4, separators=(',', ': ')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True)
    parser.add_argument('--user', default='admin')
    parser.add_argument('--password', required=True)

    main(parser.parse_args())
