# Everything (Reference)

The MCP [reference server](https://github.com/modelcontextprotocol/servers/tree/main/src/everything):
exercises every protocol feature — tools, prompts, resources, sampling. No upstream, no
secrets. Useful for verifying a new client or a Localish deployment end to end; not
something you leave installed.

The manifest pins `@modelcontextprotocol/server-everything` 2.1.0, which requires the
Node 24 runtime in the platform shim and serves stdio by default.
