# Polymarket

[caiovicentino/polymarket-mcp-server](https://github.com/caiovicentino/polymarket-mcp-server)
provides market search, prices, order books, analysis, portfolio access, and trading.
This entry starts with **wallet-free, read-only research**. Every member has a
private instance and can optionally connect their own wallet. Trading remains off
until an administrator enables it in Service Settings.

The manifest and catalog listing embed the unchanged PNG from
[Polymarket’s official site icon](https://polymarket.com/icons/apple-touch-icon.png).

Requires Localish's optional member credential support (`required: false`, added
for 0.10.0). Update Localish before installing this manifest; older versions require
credential entry even when fields are marked optional.

## Optional wallet

During app authorization, choose **Continue Without Account Details** for public
research. To add a wallet later, reconnect the MCP client using explicit consent
(`prompt=consent`) and approve access again.

- **Polygon private key:** enables wallet-backed access for that member. Stored in
  the member's instance Keychain item and injected into that instance's environment.
- **Wallet address:** optional; derived from the private key when omitted. If
  supplied, it must match. This upstream supports EOA wallets only, not proxy,
  Safe, email-login, or separate funder wallets.
- **API key, secret, and passphrase:** optionally provide all three together, with
  the private key. Otherwise the launcher derives existing nonce-zero CLOB API
  credentials or creates them when derivation fails. Derived credentials stay in
  process memory; supplied credentials stay in the member's Keychain item.

Partial API credentials or a mismatched wallet address fail startup without
printing secret inputs. The instance health check reports failed authentication.
No wallet is shared between members. Removing service consent deprovisions that
member's instance and its credentials; reconnect to replace existing credentials.

## Service settings

All settings are optional. These defaults apply across member instances:

| Setting | Default | Effect |
| --- | --- | --- |
| `ENABLE_TRADING` | `false` | Allow order creation and cancellation for members with authenticated wallets. |
| `ENABLE_AUTONOMOUS_TRADING` | `false` | Upstream orders require `confirm=true`; when enabled, the confirmation threshold applies. Requires trading enabled. |
| `MAX_ORDER_SIZE_USD` | `1000` | Upstream maximum order size. |
| `MAX_TOTAL_EXPOSURE_USD` | `5000` | Upstream total exposure limit. |
| `MAX_POSITION_SIZE_PER_MARKET` | `2000` | Upstream position limit per market. |
| `MIN_LIQUIDITY_REQUIRED` | `10000` | Upstream minimum market liquidity. |
| `MAX_SPREAD_TOLERANCE` | `0.05` | Maximum spread fraction, from 0 to 1. |
| `REQUIRE_CONFIRMATION_ABOVE_USD` | `500` | Confirmation threshold when autonomous trading is enabled. |
| `LOG_LEVEL` | `WARNING` | Upstream logging level. |

`confirm=true` is an upstream tool argument, not a separate Localish approval
screen. Risk controls are enforced by the pinned upstream implementation.
`CANCEL_ON_SHUTDOWN=false` is enforced so closing a session or health probe cannot
cancel open orders. A wallet-free member retains public research even when an
administrator enables trading.

## Tools and consent

Public mode exposes 22 upstream research/monitoring tools plus `check_connection`.
An authenticated wallet adds portfolio, order-query, and account subscription tools
(37 tools total), while trading enables the remaining eight tools (45 total).
The holder-analysis placeholder is always excluded. The launcher enforces the same
boundary on direct calls, including calls with `confirm=true`.

The manifest requests `polymarket:read` and `polymarket:trade` because it can support
both. Updates from the public-only entry require renewed consent. Localish scopes
describe authority; the launcher's settings and wallet checks filter tools.

## Runtime and health

The stdio service uses `uvx`, Python 3.12, and upstream commit
[`21f65f319ff0fc4250ea1e5094581761906839e1`](https://github.com/caiovicentino/polymarket-mcp-server/tree/21f65f319ff0fc4250ea1e5094581761906839e1)
(version 0.2.0). Dependencies resolve within upstream's constraints. The 300-second
startup allowance covers initial downloads; Localish persists its package cache.
There is no service data volume. WebSocket subscriptions last for their MCP session.

Connections include Polymarket's Gamma, CLOB and Data APIs, public/account WebSocket
endpoints, GitHub, and PyPI. The launcher prevents upstream demo-mode credential
creation. With a wallet it also supplies derived credentials to account WebSockets.

`check_connection` requests one live trending market and, when a wallet is
configured, checks authenticated open-order access without placing or cancelling
orders. Upstream JSON/text failures become MCP `isError` results, so public API
success cannot conceal wallet authentication failure. This probe does not prove
every endpoint, subscription, or trading operation works.

## Validation

Run `python3 -B scripts/check_polymarket.py` with `uvx` available. Tests use the
manifest's pinned package and synthetic credentials with mocked authenticated API
calls. They cover optional setup, modes, direct-call restrictions, credential reuse,
health failures, and settings. They never place trades or require a funded wallet.
