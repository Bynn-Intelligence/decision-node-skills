> ## Documentation index
> DecisionNode documentation: https://docs.decisionnode.com
> API: `POST https://api.decisionnode.com/v1/decide`, `GET https://api.decisionnode.com/v1/models`

# Onboard your agent to DecisionNode

> Official instructions that install the DecisionNode skill and connect the
> DecisionNode MCP server to your coding agent in one pass.

These are official instructions from Bynn Intelligence for setting up an
environment that integrates DecisionNode: fast, calibrated yes-or-no, choice and
score decisions. They are published at
`https://github.com/Bynn-Intelligence/decision-node-skills/blob/main/agent-setup.md`,
so you can verify their origin before following them.

Complete the steps yourself by running the commands directly. The exceptions are
the steps marked **User step**: in-session commands and handling the API key
happen on the user's side. Never run a command that blocks on an interactive
prompt, and never ask the user to paste an API key into the chat.

Every command below is safe to re-run.

***

## What gets installed

| Piece | What it is |
|---|---|
| Plugin `decisionnode` | The `decisionnode` skill: question types, writing state and questions, reading probabilities, batching, images, errors, the SDKs, the `dn` CLI and the MCP server |
| MCP server `decisionnode` | Seven tools: `guide`, `truth`, `choice`, `score`, `decide`, `decide_many`, `models` |

The skill installs no key. The MCP server needs a DecisionNode API key, in one of
two forms:

| Form | Address | Key |
|---|---|---|
| Hosted | `https://mcp.decisionnode.com`, Streamable HTTP | Header `Authorization: Bearer <key>` |
| Local | `uvx bynn-decisionnode-mcp`, stdio | `DECISIONNODE_API_KEY` in the server's environment |

The hosted endpoint is the **root path**. Do not append `/mcp`. Use the local
server when the client cannot send a header, when you need to pass images by local
file path, or when you point at a self-hosted DecisionNode (`DECISIONNODE_BASE_URL`).
The local server needs `uv` (`https://docs.astral.sh/uv/`).

> **User step.** Ask the user to export `DECISIONNODE_API_KEY` in the shell profile
> that launches the agent, or to put it in the client's secret store. Check that it
> is set with `test -n "$DECISIONNODE_API_KEY" && echo set`; never print it.

***

## Claude Code

The plugin installs the skill and registers the hosted MCP server, which reads
`DECISIONNODE_API_KEY` from the environment:

```
claude plugin marketplace add Bynn-Intelligence/decision-node-skills
claude plugin install decisionnode@decisionnode
```

Verify:

```
claude plugin list | grep -A2 'decisionnode@decisionnode'
```

Expect it to be listed as enabled. If it is disabled, run
`claude plugin enable decisionnode@decisionnode`.

To connect the server without the plugin, or with another scope:

```sh
# hosted
claude mcp add --transport http decisionnode https://mcp.decisionnode.com \
  --header "Authorization: Bearer $DECISIONNODE_API_KEY"

# local
claude mcp add decisionnode -e DECISIONNODE_API_KEY="$DECISIONNODE_API_KEY" -- uvx bynn-decisionnode-mcp
```

Add `-s user` for every project. Never commit a file holding a literal key.

> **User step.** Ask the user to run `/reload-plugins` (or restart Claude Code),
> then `/mcp` to confirm `decisionnode` is connected.

***

## Other agents

First install the skill:

```
npx -y skills add Bynn-Intelligence/decision-node-skills --skill '*' --yes --global
```

Then connect the MCP server for the agent in question.

### Cursor

`~/.cursor/mcp.json`, or `.cursor/mcp.json` for one project:

```json
{
  "mcpServers": {
    "decisionnode": {
      "url": "https://mcp.decisionnode.com",
      "headers": { "Authorization": "Bearer ${env:DECISIONNODE_API_KEY}" }
    }
  }
}
```

### VS Code (GitHub Copilot)

`.vscode/mcp.json`. The key is asked for once and kept in VS Code's secret storage:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "decisionnode-key",
      "description": "DecisionNode API key",
      "password": true
    }
  ],
  "servers": {
    "decisionnode": {
      "type": "http",
      "url": "https://mcp.decisionnode.com",
      "headers": { "Authorization": "Bearer ${input:decisionnode-key}" }
    }
  }
}
```

### Windsurf

`~/.codeium/windsurf/mcp_config.json`, with the local server:

```json
{
  "mcpServers": {
    "decisionnode": {
      "command": "uvx",
      "args": ["bynn-decisionnode-mcp"],
      "env": { "DECISIONNODE_API_KEY": "<key>" }
    }
  }
}
```

### Zed

In Zed's `settings.json`, under `context_servers`:

```json
{
  "context_servers": {
    "decisionnode": {
      "source": "custom",
      "command": "uvx",
      "args": ["bynn-decisionnode-mcp"],
      "env": { "DECISIONNODE_API_KEY": "<key>" }
    }
  }
}
```

### Claude Desktop

`claude_desktop_config.json` (Settings, Developer, Edit Config), with the local
server:

```json
{
  "mcpServers": {
    "decisionnode": {
      "command": "uvx",
      "args": ["bynn-decisionnode-mcp"],
      "env": { "DECISIONNODE_API_KEY": "<key>" }
    }
  }
}
```

> **User step.** For Windsurf, Zed and Claude Desktop, ask the user to put their key in place
> of `<key>` themselves, then restart the app.

### Clients that only speak stdio

Use the local server as above, or bridge to the hosted one:

```json
{
  "mcpServers": {
    "decisionnode": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.decisionnode.com", "--header", "Authorization:${AUTH_HEADER}"],
      "env": { "AUTH_HEADER": "Bearer <key>" }
    }
  }
}
```

### Headless and CI

Read the key from the CI secret store into `DECISIONNODE_API_KEY`, then:

```sh
claude mcp add --transport http decisionnode https://mcp.decisionnode.com \
  --header "Authorization: Bearer $DECISIONNODE_API_KEY"
```

or pass a config file to a single run:

```sh
cat > mcp.json <<'EOF'
{ "mcpServers": { "decisionnode": { "type": "http", "url": "https://mcp.decisionnode.com",
  "headers": { "Authorization": "Bearer ${DECISIONNODE_API_KEY}" } } } }
EOF
claude -p "..." --mcp-config mcp.json
```

For scripts with no agent at all, use the `dn` CLI or an SDK instead of MCP.

***

## Verify end to end

1. Call `guide`. It makes no API call, so it proves the transport works.
2. Call `models`. It is free and needs a valid key, so it proves the key reached
   the API. An `authentication_error` here means the key is missing or wrong, or the
   header never reached the server: check the variable and the client config, do not
   retry blindly.

These prove the MCP server only. Confirm the skill separately: on Claude Code with
`claude plugin list`, elsewhere by checking that the `decisionnode` skill is listed
by `npx skills list`. A connected server with no skill means the agent starts work
without the guidance it needs.

***

## Report the result

Report only what you verified, one line per piece:

```
DecisionNode setup
  [ok]     skill        decisionnode installed
  [ok]     MCP server   connected, models answered
  [action] reload       restart the agent to load the skill
```

Use `[ok]` for verified, `[action]` for a step the user must take, `[failed]` for a
failure, and follow every non-`[ok]` line with the exact next step.

***

## Resources

| Resource | URL |
|---|---|
| This repository | `https://github.com/Bynn-Intelligence/decision-node-skills` |
| Documentation | `https://docs.decisionnode.com` |
| API | `https://api.decisionnode.com` |
| Hosted MCP server | `https://mcp.decisionnode.com` |
| Agent Skills specification | `https://agentskills.io` |
