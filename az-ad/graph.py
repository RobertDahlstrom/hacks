#!/usr/bin/env python3

import adal
import requests

import graph_config as config

# TODO: Get this in version control
# TODO: Document app registration required, including permissions
# TODO: Turn it into something useful? ;)

# This requires an application registration in Azure and updated graph_config.py to configure client id & client secret
context = adal.AuthenticationContext(config.GRAPH_AUTHORITY)
token = context.acquire_token_with_client_credentials(
    config.API_BASE,
    config.client_id,
    config.client_secret
    )

# After authentication we can issue requests to the API as long as we include the token
headers = {
    'Authorization': 'Bearer {token}'.format(token=token["accessToken"]),
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# TODO: Add filter command to only select what we want
# ?$filter=
request_url = config.GRAPH_API_ENDPOINT.format(endpoint='auditLogs/signIns')
response = requests.get(url=request_url, headers=headers)
print(response.json())
