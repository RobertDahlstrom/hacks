#!/usr/bin/env python3

import argparse
import requests
from natsort import natsorted
import json


class Nexus(object):
    def __init__(self, username, password):
        self.auth = (username, password)
        self.base_url = 'https://nexus.electrolux.io/repository/electrolux-docker-registry/v2'
        self.manifest_headers = {
            'accept': 'application/vnd.docker.distribution.manifest.v2+json'
        }

    def clean_releases_matching(self, name, version_prefix):
        # Grab list of tags for the given name
        response = requests.get("{}/{}/tags/list".format(self.base_url, name), auth=self.auth)

        tags = response.json()['tags']
        tags_matching_prefix = filter(lambda x: x.startswith(version_prefix), tags)

        print(tags)

        manifests_url = "{}/{}/manifests".format(self.base_url, name)
        for tag in natsorted(tags_matching_prefix, key=lambda y: y.lower(), reverse=True):

            print(tag)
            # Grab the manifest for this tag...
            response = requests.get("{}/{}".format(manifests_url, tag), auth=self.auth, headers=self.manifest_headers)
            response.raise_for_status()

            # print(json.dumps(response.json(), indent=4, sort_keys=True))
            digest = response.json()['config']['digest']

            print(digest)
            # print("About to delete version: {} with digest: {}".format(tag, digest))
            response = requests.delete('{}/{}'.format(manifests_url, digest), auth=self.auth)
            response.raise_for_status()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', default="robert.dahlstrom")
    parser.add_argument('--password', required=True)
    parser.add_argument('name')
    parser.add_argument('version_prefix')

    args = parser.parse_args()

    nexus = Nexus(args.username, args.password)
    nexus.clean_releases_matching(args.name, args.version_prefix)

    # ./nexus.py edp/blackbox-exporter v0.12
