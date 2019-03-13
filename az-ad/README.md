# az-ad

Intended as a quick hack do configure groups in Azure AD.

Internally it uses the az cli and not the Graph API. Eventually this should be migrated to use the graph api instead.

In order to use you will need to:
 
 1. az login

    `az login -t <tenant id> --allow-no-subscriptions`

 2. Provide a json file with users, e.g. from JIRA REST API
    
    `https://<jira host>/rest/api/2/user/search?username=.&maxResults=1000`