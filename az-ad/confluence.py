#!/usr/bin/env python3

import argparse
import subprocess

import requests

import azure_wrapper


class Confluence(object):
    # https://<host>/rest/api/group/confluence-administrators/member?expand=status

    def __init__(self, host, auth) -> None:
        self.base_url = 'https://{host}/rest/api'.format(host=host)
        self.auth = auth

    def get_members_in_group(self, group):
        return self._json_request('/group/{group}/member?expand=status'.format(group=group))

    def get_groups(self):
        return self._json_request('/group')

    def _json_request(self, relative_url):
        url = "{base_url}{relative_url}".format(base_url=self.base_url, relative_url=relative_url)
        request = requests.get(url, auth=self.auth)
        request.raise_for_status()
        return request.json()

    @staticmethod
    def get_active_users_from_result(result):
        filtered = []
        for item in result['results']:
            if item['status'] == 'current':
                item['emailAddress'] = item['username']
                filtered.append(item)
        return filtered


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True)
    parser.add_argument('--user', default='admin')
    parser.add_argument('--password', required=True)

    args = parser.parse_args()
    confluence = Confluence(args.host, (args.user, args.password))

    groups = confluence.get_groups()
    for group in groups['results']:
        name = group['name']

        if name in ['confluence-users', 'confluence-administrators', 'jira-software-users', 'jira-administrators']:
            print("-- Ignored group: {name}".format(name=name))
            continue

        result = confluence.get_members_in_group(name)

        # Use this to display all groups with member counts
        # print('{name} - {count}'.format(name=name, count=len(result['results'])))
        # continue

        try:
            group_info = azure_wrapper.get_group(name)
        except subprocess.CalledProcessError:
            group_info = None

        if group_info:
            old_group = name
            new_group = group_info['displayName']

            # SQL to update permissions AND group names
            rename_group_sql = """UPDATE spacepermissions SET permgroupname = '{new_group}' 
            WHERE permgroupname = '{old_group}';
            UPDATE content_perm SET groupname = '{new_group}' 
            WHERE groupname IN ('old_group');
            UPDATE cwd_group SET group_name = '{new_group}', lower_group_name = '{new_group_lower}' 
            WHERE group_name = '{old_group}';""".format(
                new_group=new_group, old_group=old_group, new_group_lower=new_group.lower()
            ).strip()

            # This outputs SQL to stdout, should be captured in a file and then run
            print('-- {group} -> {name}'.format(group=old_group, name=new_group))
            print(rename_group_sql)

    # print(json.dumps(confluence.get_active_users_from_result(result), indent=4, separators=(',', ': ')))

