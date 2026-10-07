# DecisionNode

Skill for integrating [DecisionNode](https://decisionnode.com): fast, calibrated
yes-or-no (`truth`), `choice` and `score` decisions, with probabilities your code can
branch on. Bundles the DecisionNode MCP server.

## Install

```
/plugin marketplace add Bynn-Intelligence/decision-node-skills
/plugin install decisionnode@decisionnode
```

Any agent, via the skills CLI:

```bash
npx skills add Bynn-Intelligence/decision-node-skills --skill decisionnode
```

## Connect the MCP server

The plugin registers `https://mcp.decisionnode.com` and sends
`Authorization: Bearer ${DECISIONNODE_API_KEY}`, so export the key before starting
the agent:

```bash
export DECISIONNODE_API_KEY=...
```

To run the server on your machine instead: `uvx bynn-decisionnode-mcp` with the same
variable. Per-client setup is in
[agent-setup.md](https://github.com/Bynn-Intelligence/decision-node-skills/blob/main/agent-setup.md).

## Skills

| Skill | Covers |
|---|---|
| `decisionnode` | Question types, writing state and questions, reading answers, `decide` and `decide_many`, images, errors and retries, the SDKs, the `dn` CLI and the MCP server. |

## Credentials

No credential ships with this plugin. The key comes from the environment and is
sent only to DecisionNode.

## Documentation

`https://docs.decisionnode.com`
