# Polymarket

[caiovicentino/polymarket-mcp-server](https://github.com/caiovicentino/polymarket-mcp-server)
provides prediction-market search, prices, order books, market analysis, and public
WebSocket monitoring. This catalog entry exposes **22 public tools** with the
`polymarket:read` scope. It needs no wallet, API key, or member credentials.

Each member gets a private instance. The service uses Localish's stdio shim and
`uvx` with Python 3.12. The upstream source is pinned to
[`21f65f319ff0fc4250ea1e5094581761906839e1`](https://github.com/caiovicentino/polymarket-mcp-server/tree/21f65f319ff0fc4250ea1e5094581761906839e1)
(package version 0.2.0). Transitive Python dependencies resolve within upstream's
declared constraints. The 300-second startup allowance accommodates the first
Python/package download; Localish persists its package cache across restarts.

## Read-only behavior

The manifest contains a small Python launcher because upstream's `DEMO_MODE` still
attempts to create API credentials. The launcher forces demo configuration, clears
L2 credentials, blocks API credential creation, and permits only discovery,
analysis, and public monitoring tools. Direct calls to trading, portfolio, and
account subscription tools return MCP errors. No wallet credentials are requested
or used. The holder-analysis placeholder is omitted because it requires
authentication. Upstream's demo key is a public placeholder, not a wallet to fund.

`CANCEL_ON_SHUTDOWN=false` prevents order cancellation when Localish closes an MCP
session or its health probe. `ENABLE_AUTONOMOUS_TRADING=false` is also explicit;
the tool allowlist and authentication guard enforce this entry's read-only access.
Changing the demo environment variable alone does not enable trading. A trading
integration needs a separately reviewed manifest with credentials and accurate
consent scopes; Localish scopes do not filter individual tools.

## Connections and health

The service connects over HTTPS to Polymarket's public Gamma and CLOB APIs
(`gamma-api.polymarket.com`, `clob.polymarket.com`) and to
its public WebSocket endpoints (`ws-subscriptions-clob.polymarket.com` and
`ws-live-data.polymarket.com`). Installation also downloads the pinned source from
GitHub and Python packages from PyPI through `uvx`.

The health tool requests one trending market from the live Gamma API. The launcher
converts upstream JSON/text error responses to MCP `isError`, so failed API calls
report degraded health. This probe checks public market access; it does not prove
every analysis endpoint or a live WebSocket subscription works.

Monitoring subscriptions belong to the current MCP session and end when that
session closes. There is no service data volume. `LOG_LEVEL=WARNING` reduces
routine upstream logging; the entry has no operator settings or secrets.

## Validation

Run `python3 -B scripts/check_polymarket.py` from the catalog root with `uvx`
available. It resolves the manifest's pinned package and runs offline regression
checks for credential suppression, tool authorization, and MCP error reporting.
It does not place trades or require a wallet.
