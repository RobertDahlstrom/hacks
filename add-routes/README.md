# add-routes

This is a very simple script to add routes for a specific gateway.

The original use case was to add routes to a VPN tunnel after the tunnel was connected.

## Configuration
routes.py defaults to reading `routes.config.yaml` in the current directory.
It should be on this format:

```
routes:
  host_check_gateway: example.com
  hosts_to_route:
    - first.host.com
    - second.host.com
```

where

* host_check_gateway

    is a host already configured by the VPN tunnel (used to get gateway)

* hosts_to_route 

    is a list of host names to route through the same gateway as example.com uses.