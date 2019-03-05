import abc
import os.path
import re
import subprocess

import requests
import yaml
from lxml import html

"""
Various 'spiders' that know how to retrieve version information from different sources.

"""


def _beautify_version(version, beautify):
    """
    Attempts to return the numerical part of a version by stripping away common prefix and postfix notation
    E.g. release- or v or x.y.z-just-some-annoying-text
    """
    if not beautify:
        return version

    beautiful_version = version.lstrip('v')
    if beautiful_version.startswith('release-'):
        beautiful_version = beautiful_version[len('release-'):]

    if '-' in beautiful_version:
        parts = beautiful_version.split('-')
        beautiful_version = parts[0]

    return beautiful_version


def _get_version_from_metadata_label(yaml_data):
    if 'labels' not in yaml_data['metadata']:
        raise ValueError('Key: labels not found in metadata for {name}'.format(name=yaml_data['metadata']['name']))

    labels = yaml_data['metadata']['labels']

    if not ('app.kubernetes.io/version' in labels or 'apps.kubernetes.io/version' in labels):
        raise ValueError('Key: app.kubernetes.io/version not found in labels for {name}'.format(
            name=yaml_data['metadata']['name'])
        )

    if 'app.kubernetes.io/version' in labels:
        return labels['app.kubernetes.io/version']
    else:
        return labels['apps.kubernetes.io/version']


class AbstractSpider(abc.ABC):

    """
    Base class for all spiders
    """
    @abc.abstractmethod
    def get_version(self, beautify):
        pass


class AlpinePackageSpider(AbstractSpider):
    """
    Grab the latest (only?) version for an alpine package that exists for specific alpine version
    """
    def __init__(self, name, branch) -> None:
        url = "https://pkgs.alpinelinux.org/packages?name={name}&branch={branch}&arch=x86_64"
        self.url = url.format(name=name, branch=branch)

    def get_version(self, beautify):
        response = requests.get(self.url)
        response.raise_for_status()
        tree = html.fromstring(response.content)
        version_list = tree.xpath('//td[@class="version"]/text()')
        return _beautify_version(version_list[0], beautify)


class BitbucketReleaseSpider(AbstractSpider):
    """
    Retrieve version from a Bitbucket tags (only looking at top two ones, discarding latest)
    Assumes tag list is sorted in a meaningful manner when it relates to versions
    """
    def __init__(self, owner, repository):
        api = "https://api.bitbucket.org/2.0/repositories/{owner}/{repository}/refs/tags?sort=-name"
        self.url = api.format(owner=owner, repository=repository)

    def get_version(self, beautify):
        response = requests.get(self.url)
        response.raise_for_status()
        data = response.json()
        candidate = data['values'][0]
        if candidate['name'] == 'latest':
            candidate = data['values'][1]

        return _beautify_version(candidate['name'], beautify)


class DockerfileSpider(AbstractSpider):
    """
    Retrieve version from a local Dockerfile (parse the Dockerfile FROM entry)
    """
    def __init__(self, path):
        self.path = path
        self.re = re.compile('^FROM .*:v?(\d+.*)$')
 
    def get_version(self, beautify):
        """
        Expects a Dockerfile with this format:
        FROM jada/jada:1.2.3
        """
        with open(os.path.expanduser(self.path)) as f:
            for line in f:
                match = self.re.match(line)
                if match:
                    return _beautify_version(match.group(1), beautify)

        raise ValueError("No version found in {path}".format(path=self.path))


class DockerHubSpider(AbstractSpider):
    """
    Retrieve version from Docker hub tags list (only look at the top two ones, discarding latest)
    """
    def __init__(self, owner, name):
        self.owner = owner
        self.name = name
        api = "https://registry.hub.docker.com/v2/repositories/{owner}/{name}/tags/"
        self.url = api.format(owner=self.owner, name=self.name)

    def get_version(self, beautify):
        response = requests.get(self.url)
        response.raise_for_status()

        data = response.json()
        candidate = data['results'][0]
        if candidate['name'] == 'latest':
            candidate = data['results'][1]

        return _beautify_version(candidate['name'], beautify)


class GithubReleaseSpider(AbstractSpider):
    """
    Retrieve version for the latest release of a Github project using the Github API
    """
    def __init__(self, owner, repository):
        api = 'https://api.github.com/repos/{owner}/{repository}/releases/latest'
        self.url = api.format(owner=owner, repository=repository)

    def get_version(self, beautify):
        """Response contains a Github release API response and since we request latest the tag_name will correspond
        to the actual latest available version"""
        response = requests.get(self.url)
        response.raise_for_status()
        return _beautify_version(response.json()['tag_name'], beautify)


class GithubMixedReleaseSpider(AbstractSpider):
    """
    Github release spider assumes latest is the latest. Some repositories mix multiple major versions in their releases
    """
    def __init__(self, owner, repository, major):
        api = 'https://api.github.com/repos/{owner}/{repository}/releases'
        self.url = api.format(owner=owner, repository=repository)
        self.major = major

    def get_version(self, beautify):
        response = requests.get(self.url)
        response.raise_for_status()
        data = response.json()
        for release in data:
            version = _beautify_version(release['tag_name'], True)
            if version.startswith(self.major):
                return version if beautify else release['tag_name']

        raise ValueError("Failed to locate a release matching major version: {major}".format(major=self.major))


class JenkinsStableSpider(AbstractSpider):
    """
    Retrieve version for the latest stable Jenkins release (parse the published LTS changelog)
    """
    def __init__(self):
        self.url = "https://jenkins.io/changelog-stable/"

    def get_version(self, beautify):
        """
        XPath version scanner for the Jenkins Stable/LTS change log page
        Usually the version there begins with a v
        """
        response = requests.get(self.url)
        response.raise_for_status()
        tree = html.fromstring(response.content)
        version_list = tree.xpath('//div[@class="ratings"]/h3[1]/@id')
        return _beautify_version(version_list[0], beautify)


class KubernetesVersionLabelSpider(AbstractSpider):
    """
    Retrieve version from a running k8s deployment assuming it's been labeled with app.kubernetes.io/version
    """
    def __init__(self, item, name, namespace):
        self.item = item
        self.name = name
        self.namespace = namespace

    def get_version(self, beautify):
        kubectl_command = "kubectl get {item} {name} -n {namespace} -o yaml".format(
            item=self.item, name=self.name, namespace=self.namespace
        )
        result = subprocess.run(kubectl_command, shell=True, check=True, stdout=subprocess.PIPE, encoding='utf-8')
        data = yaml.load(result.stdout)
        return _beautify_version(_get_version_from_metadata_label(data), beautify)


class KubernetesImageVersionSpider(AbstractSpider):
    """
    Retrieves version from a running k8s resource using the provided pattern to boil down to the resource image spec
    For a stateful set the pattern could be: spec.template.spec.containers.0.image
    This spider does support numeric indexes used for list items.
    """
    def __init__(self, item, name, namespace, pattern):
        self.item = item
        self.name = name
        self.namespace = namespace
        self.pattern = pattern

    def get_version(self, beautify):
        kubectl_command = "kubectl -n {namespace} get {item} {name} -o yaml".format(
            namespace=self.namespace, item=self.item, name=self.name
        )
        result = subprocess.run(kubectl_command, shell=True, check=True, stdout=subprocess.PIPE, encoding='utf-8')
        data = yaml.load(result.stdout)
        section = data
        for p in self.pattern.split('.'):
            if isinstance(section, list):
                p = int(p)

            section = section[p]

        # Here we expect section to contain the image only, e.g. "quay.io/prometheus/prometheus:v2.2.1"
        (_, version) = section.split(':')
        return _beautify_version(version, beautify)


class SonarQubeReleaseSpider(AbstractSpider):
    """
    Retrieves version using SonarQubes download pages (HTML scrape). Hopefully somewhat stable page.
    """
    def __init__(self):
        self.url = "https://www.sonarqube.org/downloads/"

    def get_version(self, beautify):
        """
        XPath version scanner for the SonarQube Download page. Usually it's the first download link on the page.
        Actual version is then parsed from the download link.
        """
        response = requests.get(self.url)
        response.raise_for_status()
        tree = html.fromstring(response.content)
        download_links = tree.xpath('//a[@class="btn btn-primary"]/@href')
        (_, version_part) = download_links[0].split('-')
        version = version_part[:-4]  # Remove .zip extension
        return _beautify_version(version, beautify)


class NASpider(AbstractSpider):
    """
    Very crude N/A spider. Mostly useful while developing
    """
    def get_version(self, beautify):
        return "N/A"
