# DecisionNode Agent Skills

The official [Agent Skill](https://agentskills.io) and Claude Code plugin for
**DecisionNode**: fast, calibrated yes-or-no, choice, score, number, point and box
decisions for applications and agents. It teaches a coding agent to integrate
DecisionNode well, and connects the DecisionNode docs MCP server so the agent can
look up the current documentation while it works.

Works with Claude Code, Cursor, Codex, Copilot, Gemini CLI, OpenCode, Windsurf, Zed,
and every other agent the `skills` CLI supports.

## Onboard an agent in one shot

Point any coding agent at [`agent-setup.md`](agent-setup.md) and it installs the
skill and connects the docs MCP server itself:

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

Claude Code, with the bundled docs MCP server:

```
/plugin marketplace add Bynn-Intelligence/decision-node-skills
/plugin install decisionnode@decisionnode
```

## Set the key

The code the agent writes reads one environment variable:

```bash
export DECISIONNODE_API_KEY=...
```

Nothing in this repository ships or stores a key, and the docs MCP server needs
none.

## What is in here

| Skill | Covers |
|---|---|
| `decisionnode` | Choosing `truth`, `choice`, `score`, `number`, `point` or `box`; writing the state and the questions; reading probabilities and confidence; several questions in one `decide`; `decide_many`, batches and sessions; images and videos; boosters and their evidence; fine-tuned model names; errors and retries; the SDKs and the `dn` CLI. |

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

## Connect the docs MCP server

`npx skills add` copies skill files only. The Claude Code plugin registers the docs
server for you. Elsewhere, connect it yourself:

```bash
claude mcp add --transport http decisionnode-docs https://decisionnode.com/mcp
```

No key and no sign-in. Other clients are in [`agent-setup.md`](agent-setup.md).
The server reads the documentation; it does not make decisions, which your code
makes through the API, an SDK or the `dn` CLI.

| Tool | Does |
|---|---|
| `search_docs` | Searches every page and heading of the docs |
| `read_doc` | Returns one page as Markdown |

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

`https://decisionnode.com/docs`

## License

MIT. See [LICENSE](LICENSE).
