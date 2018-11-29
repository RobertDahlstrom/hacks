#!/usr/bin/env python3
import argparse
import colorama
import importlib
import yaml


class VersionInfo(object):
    """
    Class wrapping version information (name, current and latest versions)
    """
    def __init__(self, name, current_version, latest_versions):
        self.name = name
        self.current_version = current_version
        self.latest_version = latest_versions


def get_version(config):
    """
    Dynamically creates a spider from the given configuration and invokes said spiders get_version method
    """
    spider_class = getattr(importlib.import_module("spiders"), config['name'])
    spider = spider_class(**config['params'])
    return spider.get_version()


def scan_for_versions(config):
    """
    Returns an iterator to help retrieve versions for all configured items
    """
    for conf in config:
        yield VersionInfo(conf['name'], get_version(conf['current']), get_version(conf['latest']))


def display_item(version_info):
    """
    Colored console output of a VersionInfo object.
    """
    output = "{name}: {color}{versions}{reset}"
    versions = "{info.current_version} -> {info.latest_version}".format(info=version_info)
    color = colorama.Fore.GREEN
    if version_info.current_version != version_info.latest_version:
        color = colorama.Fore.RED
    print(output.format(name=version_info.name, color=color, versions=versions, reset=colorama.Style.RESET_ALL))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml", help="Specify your own configuration file")
    args = parser.parse_args()

    colorama.init()

    with open(args.config) as stream:
        config_yaml = yaml.safe_load(stream)

    configuration = sorted(config_yaml['versions'], key=lambda x: x['name'])

    for item in scan_for_versions(configuration):
        display_item(item)
