#!/usr/bin/env python3
import argparse
import importlib
import logging
import yaml


def get_version(config):
    spider_class = getattr(importlib.import_module("spiders"), config['name'])
    spider = spider_class(**config['params'])
    return spider.get_version()


def scan_for_versions(config):
    for config in config_yaml['versions']:
        current_version = get_version(config['current'])

        latest_version = get_version(config['latest'])

        print("{name}: {current} -> {latest}".format(name=config['name'],
                                                     current=current_version,
                                                     latest=latest_version))


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
    # TODO: Enable verbose log option

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml", help="Specify your own configuration file")
    args = parser.parse_args()

    with open(args.config) as stream:
        config_yaml = yaml.safe_load(stream)

    scan_for_versions(config_yaml)
