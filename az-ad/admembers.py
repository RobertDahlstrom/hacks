#!/usr/bin/env python3
import argparse

import azure_wrapper


def main(args):
    # azure_wrapper.remove_members_from_group(args.group)
    azure_wrapper.copy_members(args.from_group, args.to_group)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser.add_argument('--group', required=True)
    parser.add_argument('--from-group', required=True)
    parser.add_argument('--to-group', required=True)
    args = parser.parse_args()

    main(args)
