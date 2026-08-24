# Localish Catalog

Community service manifests for [Localish](https://github.com/jsmecham/Localish) — the
personal MCP platform that runs your household's AI tools on your own Mac.

Each entry is one reviewed manifest file in the
[service contract](https://github.com/jsmecham/Localish/blob/main/Docs/ServiceContract.md)
format. There is no registry service and nothing to host: Localish installs straight from
this repo's raw files, and `index.yaml` is the whole API.

## Installing a service

In Localish: **Services → Add Service**, pick from the catalog list (or paste the raw URL
of any `manifest.yaml` here). Review the preview — what it runs, the scopes it defines,
the secret names it wants — and confirm. Or from the terminal:

```
localish add https://raw.githubusercontent.com/jsmecham/localish-catalog/main/services/memory/manifest.yaml
```

## What's here

| Service | Transport | Description |
|---|---|---|
| [memory](services/memory) | stdio | Per-member persistent knowledge-graph memory |
| [unifi](services/unifi) | http | UniFi Network controller — shared, read-only defaults |
| [everything](services/everything) | stdio | MCP reference server (testing/demo) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: one directory per service
with a `manifest.yaml` and a `README.md`, images digest-pinned, secrets declared by
name only, and a PR that explains what the service talks to upstream.
