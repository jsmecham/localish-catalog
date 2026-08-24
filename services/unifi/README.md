# UniFi Network

[sirkirby/unifi-network-mcp](https://github.com/sirkirby/unifi-network-mcp): query and
manage a UniFi Network controller — devices, clients, networks, firewall.

One **shared** container for the household (a network controller has one upstream
credential). You'll fill in the controller address after install, and set the local
UniFi account's username/password as secrets (make a dedicated read-only local admin on
the controller for this). Defaults ship read-only: the network create/update/delete
policies are off and tool permission mode is `confirm` — loosen deliberately, per
policy, in your own config if you want writes.
