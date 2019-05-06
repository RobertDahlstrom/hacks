#!/usr/bin/env python3
import argparse

import azure_wrapper


def main(action, left, right):
    if action not in ['add', 'remove', 'in']:
        raise ValueError("{action} is not a supported action".format(action=action))

    count = 0
    left_members = azure_wrapper.get_users_in_group(left)

    if action == 'in':
        count = len(left_members)
        right_members = azure_wrapper.get_users_in_group(right)

        in_both = [x['objectId'] for x in left_members if x in right_members]
        print("Members in both groups:")
        for user_id in in_both:
            print(user_id)
    else:
        for member in [x for x in left_members if x['objectType'] == 'User']:
            print("Will {action} {mail} in {right}...".format(action=action, mail=member['mail'], right=right), end='')
            if action == 'add':
                azure_wrapper.add_group_member(right, member['objectId'])
            elif action == 'remove':
                azure_wrapper.remove_member_from_group(right, member['objectId'])
            else:
                raise ValueError("Internal error: {action} is supposed to be valid here".format(action=action))
            count += 1
            print('Done')

    print("{count} users processed".format(count=count))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", help="Export of active users in JIRA", required=True, choices=['add', 'remove', 'in'])
    parser.add_argument("left", help="The left group to apply action with")
    parser.add_argument("right", help="The right group to apply action with")
    args = parser.parse_args()

    main(args.action, args.left, args.right)
