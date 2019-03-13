#!/usr/bin/env python3
import argparse

import azure


def main(action, left, right):
    # Grab members from left group
    left_members = azure.get_users_in_group(left)

    # For each left group member, apply action on right group
    for member in left_members:
        if action == 'add':
            azure.add_group_member(right, member['objectId'])
        elif action == 'remove':
            azure.remove_user_from_group(right, member['objectId'])
        else:
            raise ValueError("{action} is not a supported action".format(action=action))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", help="Export of active users in JIRA", required=True, choices=['add', 'remove'])
    parser.add_argument("left", help="The left group to apply action with")
    parser.add_argument("right", help="The right group to apply action with")
    args = parser.parse_args()

    main(args.action, args.left, args.right)
