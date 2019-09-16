#!/usr/bin/env python3
import argparse
import colorama
import importlib
import yaml


class VersionInfo(object):
    """
    Class wrapping version information (name, current and latest versions)
    """

    output_pattern = '{item.name:<20}{color}{item.current_version:<10}{item.latest_version:<10}{reset}'

    def __init__(self, name, current_version, latest_versions):
        self.name = name
        self.current_version = current_version
        self.latest_version = latest_versions

    def __str__(self):
        """Colored column console output of this object"""
        color = colorama.Fore.GREEN
        if self.current_version != self.latest_version:
            color = colorama.Fore.RED
        return self.output_pattern.format(item=self, color=color, reset=colorama.Style.RESET_ALL)


class Versions(object):
    def __init__(self, config_file, beautify):
        self.config = Versions._init(config_file)
        self.beautify = beautify

    @staticmethod
    def _init(config_file):
        with open(config_file) as stream:
            config_yaml = yaml.safe_load(stream)

        return sorted(config_yaml['versions'], key=lambda x: x['name'])

    def scan(self):
        for conf in self.config:
            yield VersionInfo(conf['name'], self.get_version(conf['current']), self.get_version(conf['latest']))

    def get_version(self, config):
        """
        Dynamically invoke the spider matching the given config to retrieve version
        """
        spider_class = getattr(importlib.import_module("spiders"), config['name'])
        spider = spider_class(**config['params'])
        version = 'N/A'
        try:
            version = spider.get_version(self.beautify)
        except Exception as e:
            print("Config {config} failed...".format(config=config))
            raise e

        return version


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml", help="Specify your own configuration file")
    parser.add_argument("--ugly", action="store_true", default=False, help="Do not beautify versions")
    args = parser.parse_args()

    colorama.init()

    versions = Versions(args.config, not args.ugly)
    print("{:<20}{:<10}{:<10}".format('Name', 'Current', 'Latest'))
    for item in versions.scan():
        print(item)
