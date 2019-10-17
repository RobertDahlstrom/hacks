#!/usr/bin/env python3

import argparse
from datetime import datetime
import requests


class Bitbucket(object):
    # https://docs.atlassian.com/bitbucket-server/rest/6.7.0/bitbucket-rest.html

    def __init__(self, host, auth):
        self.base_url = 'https://{host}/rest/api/1.0'.format(host=host)
        self.auth = auth

    def get_users(self):
        url = '{base}/admin/users?limit=1000'.format(base=self.base_url)
        request = requests.get(url, auth=self.auth)
        request.raise_for_status()
        return request.json()['values']

    def get_groups(self):
        url = '{base}/admin/groups?limit=1000'.format(base=self.base_url)
        request = requests.get(url, auth=self.auth)
        request.raise_for_status()
        return request.json()['values']

    def get_users_not_logged_in_for_90_days(self):
        today = datetime.now()

        users = self.get_users()
        filtered = [u for u in users if self._not_logged_in_for_90_days(u, today)]
        return sorted(filtered, key=lambda u: u['lastAuthenticationDate'])

    @staticmethod
    def _not_logged_in_for_90_days(user, today):
        if 'lastAuthenticationTimestamp' in user:
            last_authentication_timestamp = user['lastAuthenticationTimestamp']
            dt = datetime.fromtimestamp(last_authentication_timestamp / 1000.0)
            delta = today - dt
            user['lastAuthenticationDate'] = dt
            return delta.days > 90

        return False


def display_users_not_logged_in_for_90_days(args):
    bitbucket = Bitbucket(args.host, (args.user, args.password))
    for user in bitbucket.get_users_not_logged_in_for_90_days():
        print("{} ({}) - {}".format(user['name'], user['active'], user['lastAuthenticationDate']))


def main(args):
    display_users_not_logged_in_for_90_days(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True)
    parser.add_argument('--user', default='admin')
    parser.add_argument('--password', required=True)

    main(parser.parse_args())
