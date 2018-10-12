from lxml import html
import os.path
import re
import requests


class DockerfileSpider(object):
    def __init__(self, **kwargs):
        self.path = kwargs['path']
        self.re = re.compile('^FROM .*:(\d+.*)$')
 
    def get_version(self):
        """
        Expects a Dockerfile with this format:
        FROM jada/jada:1.2.3
        """
        with open(os.path.expanduser(self.path)) as f:
            for line in f:
                match = self.re.match(line)
                if match:
                    return match.group(1)

        raise ValueError("No version found in {path}".format(path=self.path))


class GithubReleaseSpider(object):
    def __init__(self, **kwargs):
        api = 'https://api.github.com/repos/{owner}/{repository}/releases/latest'
        self.url = api.format(owner=kwargs['owner'], repository=kwargs['repository'])

    def get_version(self):
        """Response contains a Github release API response and since we request latest the tag_name will correspond
        to the actual latest available version"""
        response = requests.get(self.url)
        response.raise_for_status()
        return response.json()['tag_name']


class JenkinsStableSpider(object):
    def __init__(self):
        self.url = "https://jenkins.io/changelog-stable/"

    def get_version(self):
        """
        XPath version scanner for the Jenkins Stable/LTS change log page
        Usually the version there begins with a v
        """
        response = requests.get(self.url)
        response.raise_for_status()
        tree = html.fromstring(response.content)
        version_list = tree.xpath('//div[@class="ratings"]/h3[1]/@id')
        return version_list[0].lstrip('v')
