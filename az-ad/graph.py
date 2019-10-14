#!/usr/bin/env python3 -u

import adal
import argparse
import logging
import requests
import time

import graph_config


# TODO: Document app registration required, including permissions
class Graph(object):
    """
    Graph acts as a wrapper around Microsoft Graph API with convenience methods to not have to worry about pagination
    etc.
    Main focus right now is to exract users and their last login details (auditing)
    """

    def __init__(self, config):
        self._initialize(config)
        self.headers = {
            'Authorization': 'Bearer {token}'.format(token=self.token["accessToken"]),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self._remote = '{config.API_BASE}/{config.API_VERSION}{{endpoint}}'.format(config=config)
        self.logger = logging.getLogger("graph")
        self.logger.setLevel(logging.ERROR)

    def _initialize(self, config):
        self.context = adal.AuthenticationContext(config.GRAPH_AUTHORITY)
        self.token = self.context.acquire_token_with_client_credentials(
            config.API_BASE, config.CLIENT_ID, config.CLIENT_SECRET
        )

    def get_guest_users(self) -> []:
        return self._query_for_values("/users?$filter=userType eq 'Guest'&$select=displayName,mail,id,userPrincipalName")

    def get_most_recent_sign_in(self, user_id):
        result = self._query(endpoint="/auditLogs/signIns?$filter=userId eq '{user_id}'&$top=1".format(user_id=user_id))
        return result['value'][0] if len(result['value']) == 1 else None

    def get_sign_ins(self):
        return self._query_for_values(endpoint='/auditLogs/signIns')

    def _query_for_values(self, endpoint):
        query_result = self._query(endpoint=endpoint)
        result = []
        # Retrieves ALL results, which my be paginated
        while '@odata.nextLink' in query_result:
            result.extend(query_result['value'])
            self.logger.debug("Paging, fetching next page")
            query_result = self._query(url=query_result['@odata.nextLink'])
        # Add last result to values (the result which is not paginated)
        result.extend(query_result['value'])
        return result

    def _query(self, endpoint=None, url=None):
        if url:
            request_url = url
        else:
            request_url = self._remote.format(endpoint=endpoint)

        response = requests.get(url=request_url, headers=self.headers)
        if response.status_code == 429:
            # We're throttled! Wait before retrying
            self.logger.debug("Throttled, waiting...")
            time.sleep(10)
            return self._query(url=request_url)
        response.raise_for_status()
        return response.json()


def main(args):
    logger = logging.getLogger("main")
    logger.setLevel(logging.ERROR)

    graph = Graph(graph_config)
    count = 0

    for user in sorted(graph.get_guest_users(), key=lambda u: u['mail']):
        # user has {displayName, mail, id, userPrincipalName}
        # sign_in is None or has {createdDateTime}
        sign_in = graph.get_most_recent_sign_in(user['id'])
        display_user = not sign_in if args.no_logins else True
        if display_user:
            count += 1
            sign_in_date = 'no login' if not sign_in else sign_in['createdDateTime']
            print('{name:<30} - {mail:<40} - {date}'.format(
                name=user['displayName'],
                mail=user['mail'],
                date=sign_in_date)
            )
    print("Matched {count} user(s) in total".format(count=count))


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-logins", action="store_true", default=False, help="Only output users without any login")
    args = parser.parse_args()

    main(args)
