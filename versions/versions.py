#!/usr/bin/env python3
import argparse
import colorama
import importlib
import logging
import yaml


def get_version(config):
    spider_class = getattr(importlib.import_module("spiders"), config['name'])
    spider = spider_class(**config['params'])
    return spider.get_version()


def scan_for_versions(config):
    for item in config:
        current_version = get_version(item['current'])

        latest_version = get_version(item['latest'])

        output = "{name}: {color}{versions}{reset}"
        versions = "{current} -> {latest}".format(current=current_version, latest=latest_version)
        color = colorama.Fore.GREEN
        if current_version != latest_version:
            color = colorama.Fore.RED

        print(output.format(name=item['name'], color=color, versions=versions, reset=colorama.Style.RESET_ALL))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml", help="Specify your own configuration file")
    parser.add_argument("--log", default="WARN", choices=['CRITICAL', 'ERROR', 'WARN', 'INFO', 'DEBUG'])
    args = parser.parse_args()

    colorama.init()
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=getattr(logging, args.log))

    with open(args.config) as stream:
        config_yaml = yaml.safe_load(stream)

    scan_for_versions(config_yaml['versions'])
