# The DecisionNode docs MCP server

The DecisionNode documentation is an MCP server. Connect it to a coding agent and
the agent can search the docs and read any page as Markdown while it writes the
integration. It reads the documentation only: it does not make decisions. Your code
makes them through the API, an SDK or the `dn` CLI.

| | |
|---|---|
| Address | `https://decisionnode.com/mcp` (`https://mcp.decisionnode.com` answers too) |
| Transport | Streamable HTTP, stateless: every call is a `POST` |
| Key | None, and no sign-in |
| Limits | 120 requests a minute per client address, a request body of at most 64 KB; over the rate, a `429` with `Retry-After` in seconds |

Connecting each client: [agent-setup.md](https://github.com/Bynn-Intelligence/decision-node-skills/blob/main/agent-setup.md).

```sh
claude mcp add --transport http decisionnode-docs https://decisionnode.com/mcp
```

## Tools

Both read-only, and the same call gives the same answer until the docs change.

| Tool | Input | Does |
|---|---|---|
| `search_docs` | `query` (1 to 200 characters), `limit` (1 to 20, default 8) | Searches every page and heading. Each hit has its page, heading, section, URL, a snippet and the `path` to read. Every word of the query must appear in a hit. |
| `read_doc` | `path`: a `path` from a search hit, a slug such as `api/errors`, or a URL on decisionnode.com | Returns one page as Markdown: the title, the lead, every section, the code samples and the tables. An unknown path is a tool error that names the closest pages. |

## Using it well

1. Search with a few specific words ("retry after 429", "number question grid",
   "session frames"), then read the page the best hit names.
2. Prefer the docs over memory for limits, prices and field names: they change
   with releases, and the server always returns the current page.
3. For the decision call itself, follow the wire form in
   [questions.md](questions.md) or the SDK's README, and test against the API with
   a key from the environment.

Without MCP, an agent that can fetch URLs reads the same pages from
`https://decisionnode.com/llms.txt` (a map of every page) and
`https://decisionnode.com/llms-full.txt` (every page in full).
