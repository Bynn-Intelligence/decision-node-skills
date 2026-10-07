# DecisionNode Agent Skills

The official [Agent Skill](https://agentskills.io) and Claude Code plugin for
**DecisionNode**: fast, calibrated yes-or-no, choice and score decisions for
applications and agents. It teaches a coding agent to integrate DecisionNode well,
and connects the DecisionNode MCP server so the agent can ask DecisionNode while it
works.

Works with Claude Code, Cursor, Codex, Copilot, Gemini CLI, OpenCode, Windsurf, Zed,
and every other agent the `skills` CLI supports.

## Onboard an agent in one shot

Point any coding agent at [`agent-setup.md`](agent-setup.md) and it installs the
skill and connects the MCP server itself:

```
Follow https://github.com/Bynn-Intelligence/decision-node-skills/blob/main/agent-setup.md
```

It covers Claude Code, Cursor, VS Code, Windsurf, Zed, Claude Desktop, and headless
or CI setups, and tells the agent what to verify before it reports success.

## Install

Any agent:

```bash
npx skills add Bynn-Intelligence/decision-node-skills
```

Claude Code, with the bundled MCP server:

```
/plugin marketplace add Bynn-Intelligence/decision-node-skills
/plugin install decisionnode@decisionnode
```

## Set the key

Everything reads one environment variable:

```bash
export DECISIONNODE_API_KEY=...
```

Nothing in this repository ships or stores a key.

## What is in here

| Skill | Covers |
|---|---|
| `decisionnode` | Choosing `truth`, `choice` or `score`; writing the state and the questions; reading probabilities and confidence; several questions in one `decide`; `decide_many`; images; errors and retries; the SDKs, the `dn` CLI and the MCP server. |

A taste of what the agent learns to write:

```python
from decisionnode import DecisionNode, truth, choice, score

dn = DecisionNode()  # reads DECISIONNODE_API_KEY

d = dn.decide(
    state={"ticket": "I was charged twice and nobody has replied for 3 days."},
    questions={
        "route": choice("Where should this go?", {"billing": "money", "bug": "broken", "account": "login"}),
        "urgency": score("How urgent is this?", ["routine", "today", "urgent", "critical"]),
        "escalate": truth("Escalate to a human now?"),
    },
)

d["route"].choice   # "billing"
d["escalate"].truth # 0.94
```

## Connect the MCP server

`npx skills add` copies skill files only. The Claude Code plugin registers the
hosted server for you, sending `DECISIONNODE_API_KEY` as a bearer token. Elsewhere,
connect it yourself:

```bash
# hosted
claude mcp add --transport http decisionnode https://mcp.decisionnode.com \
  --header "Authorization: Bearer $DECISIONNODE_API_KEY"

# local, over stdio
claude mcp add decisionnode -e DECISIONNODE_API_KEY="$DECISIONNODE_API_KEY" -- uvx bynn-decisionnode-mcp
```

The hosted endpoint is the root path; do not append `/mcp`. Other clients are in
[`agent-setup.md`](agent-setup.md).

| Tool | Does |
|---|---|
| `guide` | How to use the other tools well. Free. |
| `truth`, `choice`, `score` | One question of that type about a state |
| `decide` | Several questions about one state, in one request |
| `decide_many` | The same questions about many states |
| `models` | The models the key may use. Free. |

## Configuration

| Setting | Environment variable | Default |
|---|---|---|
| API key | `DECISIONNODE_API_KEY` | none |
| Base URL | `DECISIONNODE_BASE_URL` | `https://api.decisionnode.com` |
| Model | `DECISIONNODE_MODEL` | `decisionnode-latest` |

## Development

```bash
python3 hooks/validate_manifests.py
python3 hooks/check_versions.py
python3 hooks/check_skills.py
```

The version in `.claude-plugin/marketplace.json`, the plugin's `plugin.json`, the
skill's front matter and `server.json` must agree; bump them together.

## Documentation

`https://docs.decisionnode.com`

## License

MIT. See [LICENSE](LICENSE).
