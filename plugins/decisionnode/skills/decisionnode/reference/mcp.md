# The DecisionNode MCP server

Lets an agent ask DecisionNode for a calibrated judgment in one tool call while it
works: "is this claim supported by the source", "which of these twenty messages
ask for a refund", "how urgent is this ticket". It is a partner to the agent's own
model for narrow judgments, not a replacement.

| | Hosted | Local |
|---|---|---|
| Address | `https://mcp.decisionnode.com` (the root path; do not append `/mcp`) | `uvx bynn-decisionnode-mcp` |
| Transport | Streamable HTTP | stdio |
| Key | `Authorization: Bearer <DecisionNode API key>` on the connection | `DECISIONNODE_API_KEY` in the server's environment |
| Images | `https` URL or base64 data (about 3 MiB of base64 per call; send larger images by URL) | Also a local file path |

Neither stores a state, a question or an answer. Every tool call that asks a
question is an API request, billed to the key like any other.

Connecting each client: [agent-setup.md](https://github.com/Bynn-Intelligence/decision-node-skills/blob/main/agent-setup.md).

## Tools

All read-only and idempotent.

| Tool | Use it to | Costs |
|---|---|---|
| `guide` | Learn how to use the other tools well | Nothing |
| `truth` | Ask one yes-or-no question about a state | A request |
| `choice` | Pick one option from a set you define | A request |
| `score` | Place the state on an ordered scale you define | A request |
| `decide` | Ask several questions of any type about one state | One request, the state counted once |
| `decide_many` | Ask the same questions about many states (1 to 50 items) | One request per item |
| `models` | List the models the key may use | Nothing |

Inputs:

| Tool | Input |
|---|---|
| `truth` | `instructions`, `state`, optional `if_true`, `if_false`, `images`, `model` |
| `choice` | `instructions`, `options` (list of names, or name to description), `state`, `images`, `model` |
| `score` | `instructions`, `levels` (lowest first), `state`, `images`, `model` |
| `decide` | `state`, `questions` (id to `{type, instructions, criteria}`), `images`, `model` |
| `decide_many` | `items` (list of `{id, state}`), `questions`, `model` |

Results: `truth` gives `{"truth": 0.94}`; `choice` gives `choice`, `confidence`,
`probabilities`; `score` gives `score`, `confidence`, `legend`, `probabilities`;
`decide` gives `{"answers", "model", "input_tokens"}`; `decide_many` gives
`{"results": {item id: {"answers"} or {"error"}}, "input_tokens"}`, and one item's
failure does not fail the call. A `safety` field appears only when the hosted check
flagged a category.

## Using it well (the same advice as the `guide` tool)

1. DecisionNode sees only what you pass: the state, the question and the images.
   It knows nothing about the conversation. Put every fact it needs in `state`.
2. Pick `truth` for yes or no, `choice` for one of a set, `score` for a degree.
3. Ask one narrow thing per question.
4. 0.5 on a `truth` means it cannot tell, not "half true". Treat the middle as
   unknown and gather more context or ask the user.
5. Several questions about one state: `decide`. The same question about many
   states: `decide_many`. Both are cheaper and faster than many single calls.
6. Use `flash` models (`decisionnode-flash-latest`) for high volume where speed and
   cost matter more than the last point of accuracy.
7. On an error, read `reason`, fix the call, and try again. Do not resend a refusal.
