# Localish Catalog

Community service manifests for [Localish](https://github.com/jsmecham/Localish) — the
personal MCP platform that runs your household's AI tools on your own Mac.

Each entry is one reviewed manifest file in the
[service contract](https://github.com/jsmecham/Localish/blob/main/Docs/ServiceContract.md)
format. There is no registry service and nothing to host: Localish installs straight from
this repo's raw files, and `index.json` is the whole API.

The catalog uses Localish's [JSON document format](https://github.com/jsmecham/Localish/blob/main/Docs/Decisions/0034-foundation-document-formats.md).

## Installing a service

In Localish: **Services → Add Service**, pick from the catalog list (or paste the raw URL
of any `manifest.json` here). Review the preview — what it runs, the scopes it defines,
the secret names it wants — and confirm. Or from the terminal:

```
localish add https://raw.githubusercontent.com/jsmecham/localish-catalog/main/services/memory/manifest.json
```

Installed services pick up manifest display names and icons through **Check for Updates**.
Review and apply the update, then restart Localish to load the saved definition.
The catalog index includes each service's available artwork for Add Service;
clients that support catalog icons show it before manifest review.

## What's here

| Service | Transport | Description |
|---|---|---|
| [memory](services/memory) | stdio | Per-member persistent knowledge-graph memory |
| [monarch](services/monarch) | stdio | Monarch Money — transactions, budgets, rules, categories |
| [unifi](services/unifi) | http | UniFi Network controller — per-member accounts, read-only defaults |
| [everything](services/everything) | stdio | MCP reference server (testing/demo) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: one directory per service
with a `manifest.json` and a `README.md`, images digest-pinned, secrets declared by
name only, and a PR that explains what the service talks to upstream.
