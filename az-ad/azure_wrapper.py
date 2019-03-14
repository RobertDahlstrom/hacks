import json
import subprocess

# TODO: Migrate this module to use the graph api instead of relying on local az cli


# Internal helper methods #
def _run(command):
    proc = subprocess.run(command, shell=True, capture_output=True, encoding='utf-8')
    proc.check_returncode()
    return json.loads(proc.stdout)


def _run_no_return(command):
    proc = subprocess.run(command, shell=True, capture_output=True, encoding='utf-8')
    proc.check_returncode()
# End internal helper methods #


# User centric functions #
def filter_users(search_filter):
    """
      Example filter query: az ad user list --filter "mail eq 'robert.dahlstrom@diabol.se'"
      TODO: Add link to page describing filter usage
    """
    command = "az ad user list --filter \"{filter}\"".format(filter=search_filter)
    return _run(command)


def find_user_by_email(email):
    """
    Search for a user by email and returns User if found, or None if no user was found
    """
    result = filter_users("mail eq '{mail}'".format(mail=email))

    if len(result) == 1:
        return result[0]

    return None


def get_member_groups(object_id):
    command = "az ad user get-member-groups --upn-or-object-id {object_id}".format(object_id=object_id)
    return _run(command)


# Group centric functions #
def add_group_member(group_name, object_id):
    if user_in_group(object_id, group_name):
        return

    command = "az ad group member add --group '{group}' --member-id {object_id}".format(
        group=group_name, object_id=object_id
    )

    _run_no_return(command)


def user_in_group(object_id, group_name):
    """
    get_member_groups:
        [{displayName: ...,objectId: ...}]
    """
    for member_group in get_member_groups(object_id):
        if member_group['displayName'] == group_name:
            return True

    return False


def get_users_in_group(group_name):
    command = "az ad group member list --group {group}".format(group=group_name)
    return _run(command)


def remove_user_from_group(group_name, object_id):
    command = "az ad group member remove --group {group} --member-id {member_id}".format(
        group=group_name, member_id=object_id
    )
    _run_no_return(command)
