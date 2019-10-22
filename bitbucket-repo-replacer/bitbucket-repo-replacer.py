#!/usr/bin/env python3

import argparse
import os
import subprocess
import requests
import yaml
import shutil
import uuid


class Bitbucket(object):
    # https://docs.atlassian.com/bitbucket-server/rest/6.7.0/bitbucket-rest.html

    def __init__(self, host, token):
        self.base_url = 'https://{host}/rest/api/1.0'.format(host=host)
        self.token = token

    def get_repos(self, project_key):
        url = '{base}/projects?limit=1000'.format(base=self.base_url)
        if project_key:
            url = '{base}/projects/{key}/repos?limit=1000'.format(
                base=self.base_url, key=project_key)

        headers = {'Authorization': 'Bearer ' + self.token}
        request = requests.get(url, headers=headers)
        request.raise_for_status()
        return request.json()['values']

    def add_reviewer(self, project_key, repo_slug, pull_request_id, username):
        data = {
            "user": {
                "name": username
            },
            "role": "REVIEWER"
        }

        url = '{base}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pull_request_id}/participants'.format(
            base=self.base_url, project_key=project_key, repo_slug=repo_slug, pull_request_id=pull_request_id
        )

        headers = {'Authorization': 'Bearer ' + self.token}
        request = requests.post(url, json=data, headers=headers)
        request.raise_for_status()
        print(request.json())

    def create_pull_request(self, project_key, repo_slug, title, description, branch):
        pr_data = {
            'title': title,
            'description': description,
            'fromRef': {
                'id': 'refs/heads/{branch}'.format(branch=branch),
                'repository': {
                    'slug': repo_slug,
                    'project': {
                        'key': project_key
                    }
                }
            }, 'toRef': {
                'id': 'refs/heads/master',
                'repository': {
                    'slug': repo_slug,
                    'project': {
                        'key': project_key
                    }
                }
            }
        }

        url = '{base}/projects/{project_key}/repos/{repo_slug}/pull-requests'.format(
            base=self.base_url, project_key=project_key, repo_slug=repo_slug
        )

        headers = {'Authorization': 'Bearer ' + self.token}
        request = requests.post(url, json=pr_data, headers=headers)
        request.raise_for_status()
        return request.json()


def find_replace(directory, patterns):
    exclude = ['.git', '.svn']
    for root, dirs, files in os.walk(os.path.abspath(directory), topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude]
        for name in files:
            try:
                filepath = os.path.join(root, name)
                with open(filepath) as f:
                    s = f.read()
                for pattern in patterns:
                    s = s.replace(pattern[0], pattern[1])
                with open(filepath, "w") as f:
                    f.write(s)
            except UnicodeDecodeError:
                pass  # Fond non-text data


def main(bitbucket, config):
    execution_id = str(uuid.uuid1())[:8]

    # Parse replacements from configuration file
    replace_patterns = []
    for replacement in config['spec']['replacements']:
        replace_patterns.append((replacement['from'], replacement['to']))

    # Create temporary directory, delete the old one if present
    dir = 'repo-replacer-temp-dir'
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.makedirs(dir)
    os.chdir(dir)

    # Finding all repositories
    for project in config['spec']['projects']:
        repos = []
        for repo in bitbucket.get_repos(project):
            ssh_clone_link = [s['href'] for s in repo['links']['clone'] if s['name'] == 'ssh']
            repos.append({'slug': repo['slug'], 'ssh': ssh_clone_link[0]})

        for repo in repos:
            # Clone repository to temporary directory
            subprocess.run(['git', 'clone', '--depth', '1', repo['ssh']])
            os.chdir(repo['slug'])
            subprocess.run(['git', 'checkout', '-b', 'repo-replacer-' + execution_id])

            # Search and replace provided values
            find_replace('.', replace_patterns)
            status = subprocess.run(['git', 'status', '--porcelain'], stdout=subprocess.PIPE, encoding='utf-8')
            if not status.stdout:
                os.chdir('..')
                continue

            # Submit pull request
            subprocess.run(
                ['git', 'commit', '-am', config['spec']['description']])
            subprocess.run(['git', 'push', 'origin', 'repo-replacer-' + execution_id])
            pull_request = bitbucket.create_pull_request(project, repo['slug'], title=config['spec']['description'],
                                                         description='', branch='repo-replacer-' + execution_id)
            print(pull_request)

            # Add reviewers to the Pull request
            reviewers = config['spec']['reviewers']
            for reviewer in reviewers or []:
                try:
                    bitbucket.add_reviewer(project_key=project, repo_slug=repo['slug'],
                                           pull_request_id=pull_request['id'],
                                           username=reviewer)
                except requests.exceptions.HTTPError as e:
                    # Don't stop execution if the reviewers assignment fails for this user
                    if e.response.status_code == 404:
                        pass

            os.chdir('..')

    # Cleanup
    os.chdir('..')
    shutil.rmtree(dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Note : to get user repositories, add a tilde before username as a project name (~user.name_site.com)
    parser.add_argument('--host', required=True)
    parser.add_argument('--token', required=True)

    args = parser.parse_args()

    with open("config.yaml", 'r') as stream:
        config = yaml.safe_load(stream)

    bitbucket = Bitbucket(args.host, args.token)

    main(bitbucket, config)
