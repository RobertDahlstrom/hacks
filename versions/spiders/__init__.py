import os.path
import re
import subprocess

import requests
import yaml
from lxml import html

"""
Various 'spiders' that know how to retrieve version information from different sources.

"""


class DockerfileSpider(object):
    """
    Retrieve version from a local Dockerfile (parse the Dockerfile FROM entry)
    """
    def __init__(self, **kwargs):
        self.path = kwargs['path']
        self.re = re.compile('^FROM .*:v?(\d+.*)$')
 
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
    """
    Retrieve version for the latest release of a Github project using the Github API
    """
    def __init__(self, **kwargs):
        api = 'https://api.github.com/repos/{owner}/{repository}/releases/latest'
        self.url = api.format(owner=kwargs['owner'], repository=kwargs['repository'])

    def get_version(self):
        """Response contains a Github release API response and since we request latest the tag_name will correspond
        to the actual latest available version"""
        response = requests.get(self.url)
        response.raise_for_status()
        return response.json()['tag_name'].lstrip('v')


class JenkinsStableSpider(object):
    """
    Retrieve version for the latest stable Jenkins release (parse the published LTS changelog)
    """
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


class KubernetesVersionLabelSpider(object):
    """
    Retrieve version from a running k8s deployment assuming it's been labeled with app.kubernetes.io/version
    """
    def __init__(self, name, namespace):
        self.name = name
        self.namespace = namespace

    def get_version(self):
        kubectl_command = "kubectl get deployment {name} -n {namespace} -o yaml".format(
            name=self.name, namespace=self.namespace
        )
        result = subprocess.run(kubectl_command, shell=True, check=True, stdout=subprocess.PIPE, encoding='utf-8')
        data = yaml.load(result.stdout)
        return data['metadata']['labels']['app.kubernetes.io/version'].lstrip('v')