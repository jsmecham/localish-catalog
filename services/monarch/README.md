# Monarch Money

[robcerda/monarch-mcp-server](https://github.com/robcerda/monarch-mcp-server): 49 tools
over your Monarch Money data — accounts, transactions, budgets, cashflow, and full
management surfaces: transaction rules (create/update/delete), category creation and
editing, tags, bulk categorization, and a needs-review queue.

Per-member containers: each household member signs in with their own Monarch account
and keeps their own session. After first consent you'll paste your Monarch cookie
header (the label walks you through DevTools); the platform verifies it against the
real API before saving, and the session persists in your instance's `data` volume.

Pinned to an upstream commit with `mcp<2` constrained (the 2.x Python SDK renamed
FastMCP; upstream declares no upper bound yet).
