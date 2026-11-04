# Memory

Anthropic's [knowledge-graph memory server](https://github.com/modelcontextprotocol/servers/tree/main/src/memory):
entities, relations, and observations that persist across conversations.

Under Localish each household member gets **their own container and their own graph** —
the `data` volume lives in that member's instance state, is covered by ordinary Mac
backups, and is deleted on offboarding. No upstream account, no secrets.

The manifest pins `@modelcontextprotocol/server-memory` 2.0.1, which requires the
Node 24 runtime in the platform shim. Review the upstream release before changing the
pin; the graph file at `MEMORY_FILE_PATH` is JSON Lines, and each write takes a lock
file beside it in the `data` volume.
