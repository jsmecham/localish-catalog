# UniFi Network

[sirkirby/unifi-network-mcp](https://github.com/sirkirby/unifi-network-mcp): query and
manage a UniFi Network controller — devices, clients, networks, firewall.

Each member receives a **private instance** connected to the household's controller.
Configure the controller address once after installation. Each member enters their
own local UniFi username and password during connection; Localish stores those
credentials in that instance's private Keychain item.

Create a separate local account in UniFi for each member and assign its Network
permissions there. Use a dedicated read-only local account for read-only access.
The pinned MCP image requires a local username and password; its experimental API
key support does not replace them. See the [pinned authentication settings](https://github.com/sirkirby/unifi-mcp/blob/c1777a4db0cba5075b5b94fa0440afaf9aec4e14/apps/network/docs/configuration.md#essential-variables).

The manifest defaults to read-only access: create, update, and delete policy gates
are off, with tool permission mode set to `confirm`. Enable writes deliberately
in the manifest, within the permissions granted to the member's UniFi account.

## Updating a shared installation

Install a Localish build with HTTP member-credential support before applying this
manifest. Review the update and restart Localish. The sharing change removes the
shared instance and its instance data; each member connects again and supplies
their own UniFi credentials.

## Icon

The manifest embeds the PNG from the [official site icon](https://ui.com/microsite/apple-touch-icon.png).
