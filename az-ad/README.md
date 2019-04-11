# az-ad

Intended as a quick hack do work with Confluence, Jira & Bitbucket, all integrated with Azure AD.

Internally it uses the REST API's of the tools as well as provides a wrapper around the az cli. Eventually this should 
be migrated to use the MS Graph API.

To get started we assume you have python3 installed and available along with pip3

 1. Install python requirements

    `pip3 install -r requirements.txt`
 
 2. Login with az so you have a valid az login session

    `az login -t <tenant id> --allow-no-subscriptions`

 3. Edit the scripts to suite your needs
 
    a. ./bitbucket.py --host <bitbucket host> --password "<admin password>"
    
    b. ./jira.py --host <jira host> --password "<admin password>"
    
    c. ./confluence.py --host <confluence host> --password "<admin password>"

For direct interaction with azure you have the ad.*.py scripts:

* adgroups.py
* admembers.py
* adusers.py

same thing there, edit them to suit your needs.
