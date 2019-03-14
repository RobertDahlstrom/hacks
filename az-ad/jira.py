#!/usr/bin/env python3

import argparse
import json
import requests


def main(args):
    url = 'https://{args.host}/rest/api/2/user/search?username={args.search}&maxResults=1000'.format(args=args)
    request = requests.get(url, auth=(args.user, args.password))
    request.raise_for_status()
    print(json.dumps(request.json(), indent=4, separators=(',', ': ')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', default='admin')
    parser.add_argument('--password', required=True)
    parser.add_argument('--host', required=True)
    parser.add_argument('--search', help="Jira username search filter", default='.')

    main(parser.parse_args())
