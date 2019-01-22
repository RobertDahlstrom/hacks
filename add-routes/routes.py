#!/usr/bin/env python3

# Given list of addresses, grab their ip's and add them to the routing table
import argparse
import re
import socket
import subprocess
import yaml


def get_ips_to_route(hosts):
    ips = []
    for host in hosts:
        ip = socket.gethostbyname(host)
        ips.append(ip)
    return ips


def get_gateway_from_host_check(host):
    result = subprocess.run(['route', '-n', 'get', host],
                            check=True, capture_output=True, encoding='UTF-8')
    match = re.search(r'^\s+gateway: (.*?)$', result.stdout, re.MULTILINE)
    return match.group(1)  # Capture group 1 is gateway ip


def add_route_for_ips(ips, gateway):
    for ip in ips:
        subprocess.run(["sudo", "route", "-n", "add", "-net", "{ip}/32".format(ip=ip), gateway], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Simple wrapper around route that does dns names to routes mappings. "
                    "Useful over VPN tunnels when routes are missing."
    )
    parser.add_argument('--config', default="routes.config.yaml", help="The config file to read")
    args = parser.parse_args()

    with open(args.config) as stream:
        config = yaml.safe_load(stream)['routes']

    ips = get_ips_to_route(config['hosts_to_route'])

    print("About to invoke sudo, please provide your password if prompted")
    gateway = get_gateway_from_host_check(config['host_check_gateway'])

    add_route_for_ips(ips, gateway)
