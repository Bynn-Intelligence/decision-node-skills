# DecisionNode

Skill for integrating [DecisionNode](https://decisionnode.com): fast, calibrated
yes-or-no (`truth`), `choice`, `score`, `number`, `point` and `box` decisions, with
probabilities your code can branch on. Bundles the DecisionNode docs MCP server.

## Install

```
/plugin marketplace add Bynn-Intelligence/decision-node-skills
/plugin install decisionnode@decisionnode
```

Any agent, via the skills CLI:

```bash
npx skills add Bynn-Intelligence/decision-node-skills --skill decisionnode
```

## The docs MCP server

The plugin registers `https://decisionnode.com/mcp`, the DecisionNode
documentation as an MCP server, with two tools: `search_docs` and `read_doc`. It
needs no key. It reads the docs; decisions are made by your code through the API,
an SDK or the `dn` CLI. Per-client setup is in
[agent-setup.md](https://github.com/Bynn-Intelligence/decision-node-skills/blob/main/agent-setup.md).

## Skills

| Skill | Covers |
|---|---|
| `decisionnode` | Question types, writing state and questions, reading answers, `decide`, `decide_many`, batches and sessions, images and videos, boosters, fine-tuned model names, errors and retries, the SDKs and the `dn` CLI. |

## Credentials

No credential ships with this plugin. The code you write reads the key from
`DECISIONNODE_API_KEY` and sends it only to DecisionNode.

## Documentation

`https://decisionnode.com/docs`
