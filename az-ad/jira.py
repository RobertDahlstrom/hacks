#!/usr/bin/env python3

import argparse
import json
import re
import subprocess

import requests

import azure_wrapper

class JIRA(object):
    def __init__(self, host, auth) -> None:
        self.base_url = 'https://{host}/rest/api/2'.format(host=host)
        self.auth = auth

    def user_search(self, search, max_results=1000):
        url = '/user/search?username={search}&maxResults={max_results}'.format(search=search, max_results=max_results)
        return self._query(url)

    def get_projects(self):
        url = '/project'
        return self._query(url)

    def get_project_roles(self, id_or_key):
        url = '/project/{id}/role'.format(id=id_or_key)
        return self._query(url)

    def query(self, url):
        return self._query(url.replace(self.base_url, ''))

    def _query(self, url):
        query_url = '{base_url}{url}'.format(base_url=self.base_url, url=url)
        request = requests.get(query_url, auth=self.auth)
        request.raise_for_status()
        return request.json()

    def _update(self, url, data):
        post_url = '{base_url}{url}'.format(base_url=self.base_url, url=url)
        request = requests.post(post_url, json=data)
        request.raise_for_status()
        return request.json()

    def add_actor_to_project_role(self, project_id_or_key, role_id, actor_to_add):
        url = '/project/{project_id_or_key}/role/{role_id}'.format(project_id_or_key=project_id_or_key, role_id=role_id)
        return self._update(url, actor_to_add)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', default='admin')
    parser.add_argument('--password', required=True)
    parser.add_argument('--host', required=True)
    parser.add_argument('--search', help="Jira username search filter", default='.')

    args = parser.parse_args()
    jira = JIRA(args.host, (args.user, args.password))
    # jira.user_search(args.search)

    # For each project, get project roles and then find assigned actors to those roles
    pattern = re.compile('[a-f0-9]+-[a-f0-9]+.*')
    projects = jira.get_projects()
    for project in projects:
        print("Checking roles in project: {project}".format(project=project['name']))
        roles = jira.get_project_roles(project['id'])
        for role, url in roles.items():
            role_details = jira.query(url)
            for actor in role_details['actors']:
                if pattern.match(actor['name']):
                    try:
                        group_info = azure_wrapper.get_group(actor['name'])
                    except subprocess.CalledProcessError:
                        group_info = None

                    if group_info:
                        print("Visit: https://{host}/plugins/servlet/project-config/{key}/roles".format(
                            host=args.host, key=project['key']
                        ))
                        print("   and assign group: {group_name}".format(group_name=group_info['displayName']))
                        actor_to_add = {"group": [group_info['displayName']]}
                        jira.add_actor_to_project_role(project['key'], role_details['id'], actor_to_add)

                        exit(-1)
                    # print(json.dumps(role_details, indent=4, separators=(',', ': ')))
