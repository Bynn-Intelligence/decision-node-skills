> ## Documentation index
> DecisionNode documentation: https://decisionnode.com/docs
> API: `POST https://api.decisionnode.com/v1/decide`, `GET https://api.decisionnode.com/v1/models`

# Onboard your agent to DecisionNode

> Official instructions that install the DecisionNode skill and connect the
> DecisionNode docs MCP server to your coding agent in one pass.

These are official instructions from Bynn Intelligence for setting up an
environment that integrates DecisionNode: fast, calibrated yes-or-no, choice,
score, number, point and box decisions. They are published at
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
| Plugin `decisionnode` | The `decisionnode` skill: question types, writing state and questions, reading probabilities, batches and sessions, images and videos, boosters, fine-tuned model names, errors, the SDKs and the `dn` CLI |
| MCP server `decisionnode-docs` | The DecisionNode documentation, with two tools: `search_docs` and `read_doc` |

The docs server is at `https://decisionnode.com/mcp` (Streamable HTTP;
`https://mcp.decisionnode.com` answers too). It needs no key and no sign-in, and
it does not make decisions: the code the agent writes makes them through the API,
an SDK or the `dn` CLI, with a key from the environment.

> **User step.** Ask the user to export `DECISIONNODE_API_KEY` in the shell profile
> that runs their application and tests, or to put it in their secret store. Keys
> start with `dn_live_` and are created in the console at
> `https://decisionnode.com/console/keys`. Check that it is set with
> `test -n "$DECISIONNODE_API_KEY" && echo set`; never print it.

***

## Claude Code

The plugin installs the skill and registers the docs MCP server:

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

To connect the docs server without the plugin, or with another scope:

```sh
claude mcp add --transport http decisionnode-docs https://decisionnode.com/mcp
```

Add `-s user` for every project.

> **User step.** Ask the user to run `/reload-plugins` (or restart Claude Code),
> then `/mcp` to confirm `decisionnode-docs` is connected.

***

## Other agents

First install the skill:

```
npx -y skills add Bynn-Intelligence/decision-node-skills --skill '*' --yes --global
```

Then connect the docs server for the agent in question.

### Cursor

`~/.cursor/mcp.json`, or `.cursor/mcp.json` for one project:

```json
{
  "mcpServers": {
    "decisionnode-docs": { "url": "https://decisionnode.com/mcp" }
  }
}
```

### VS Code (GitHub Copilot)

`.vscode/mcp.json`:

```json
{
  "servers": {
    "decisionnode-docs": { "type": "http", "url": "https://decisionnode.com/mcp" }
  }
}
```

### Claude Desktop and claude.ai

Add it as a custom connector: **Customize**, **Connectors**, **Add custom
connector**, then paste `https://decisionnode.com/mcp` and choose no sign-in.

> **User step.** Ask the user to add the connector themselves; it is a setting in
> their account.

### Windsurf, Zed and clients that only speak stdio

Bridge to the server with `mcp-remote` (needs Node). For Windsurf in
`~/.codeium/windsurf/mcp_config.json`, for Claude Desktop in
`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "decisionnode-docs": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://decisionnode.com/mcp"]
    }
  }
}
```

For Zed, the same command under `context_servers` in its `settings.json`:

```json
{
  "context_servers": {
    "decisionnode-docs": {
      "source": "custom",
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://decisionnode.com/mcp"]
    }
  }
}
```

> **User step.** Ask the user to restart the app after the change.

### Headless and CI

```sh
claude mcp add --transport http decisionnode-docs https://decisionnode.com/mcp
```

or pass a config file to a single run:

```sh
cat > mcp.json <<'EOF'
{ "mcpServers": { "decisionnode-docs": { "type": "http", "url": "https://decisionnode.com/mcp" } } }
EOF
claude -p "..." --mcp-config mcp.json
```

For scripts with no agent at all, use the `dn` CLI or an SDK.

***

## Verify end to end

1. Call `search_docs` with the query `boosters`. It needs no key, so it proves the
   transport works; expect hits with a `path` each.
2. Call `read_doc` with a `path` from a hit. Expect the page as Markdown.
3. If the user has set `DECISIONNODE_API_KEY`, prove it reaches the API with the
   free models list, printing only the status code:
   `curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $DECISIONNODE_API_KEY" https://api.decisionnode.com/v1/models`.
   Expect `200`. A `401` means the key is missing or wrong: check the variable, do
   not retry blindly.

These prove the MCP server and the key only. Confirm the skill separately: on
Claude Code with `claude plugin list`, elsewhere by checking that the
`decisionnode` skill is listed by `npx skills list`. A connected server with no
skill means the agent starts work without the guidance it needs.

***

## Report the result

Report only what you verified, one line per piece:

```
DecisionNode setup
  [ok]     skill        decisionnode installed
  [ok]     docs server  connected, search_docs answered
  [ok]     API key      models answered 200
  [action] reload       restart the agent to load the skill
```

Use `[ok]` for verified, `[action]` for a step the user must take, `[failed]` for a
failure, and follow every non-`[ok]` line with the exact next step.

***

## Resources

| Resource | URL |
|---|---|
| This repository | `https://github.com/Bynn-Intelligence/decision-node-skills` |
| Documentation | `https://decisionnode.com/docs` |
| Docs for agents without MCP | `https://decisionnode.com/llms.txt` |
| API | `https://api.decisionnode.com` |
| Docs MCP server | `https://decisionnode.com/mcp` |
| Agent Skills specification | `https://agentskills.io` |
