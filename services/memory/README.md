# Memory

Anthropic's [knowledge-graph memory server](https://github.com/modelcontextprotocol/servers/tree/main/src/memory):
entities, relations, and observations that persist across conversations.

Under Localish each household member gets **their own container and their own graph** —
the `data` volume lives in that member's instance state, is covered by ordinary Mac
backups, and is deleted on offboarding. No upstream account, no secrets.
