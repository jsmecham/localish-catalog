# Contributing a service

A catalog entry is a directory under `services/<slug>/` containing:

- `manifest.yaml` — exactly one service entry in the
  [service contract](https://github.com/jsmecham/Localish/blob/main/Docs/ServiceContract.md)
  format, keyed by the slug
- `README.md` — what the service does, what it connects to upstream, and what each
  secret/setting/credential field is for

Plus one line in the root `index.yaml`.

## Review rules

These are what a PR review checks, because they are what an operator's install preview
shows:

1. **Pin what runs.** `image:` references are digest-pinned (`…@sha256:…`), never a
   mutable tag. stdio `command:` entries pin the package version
   (`npx -y some-server@1.4.2`) once the server has stable releases.
2. **Secrets are names, never values.** `secrets:` and `credentialFields:` declare what
   the operator/member will be asked for; no value, default, or example token appears
   anywhere in the manifest.
3. **Scopes say what it can do.** Scopes render on the consent screen — write them for
   the member reading that screen (`monarch:read`, not `access`).
4. **Declare honest startup.** If cold start is slow (big npm package, first-run
   indexing), set `startupSeconds` so provisioning doesn't flap.
5. **A healthTool that proves the credential.** `initialize` succeeds even with dead
   upstream credentials; pick a real tool call that exercises them.
6. **stdio needs no image.** `transport: stdio` + `command` is the whole entry — do not
   wrap npm/PyPI servers in custom images the platform would have to trust.

Trust model: installing a service is the operator's decision, made from the preview.
The catalog's job is to make that preview truthful — nothing here is sandboxed beyond
what Localish always does (NAT-only containers, gateway-only ingress, per-member
isolation).
