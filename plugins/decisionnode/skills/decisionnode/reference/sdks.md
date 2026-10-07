# SDKs

Every SDK has the same surface and the same behaviour; only the spelling follows
the language. Each reads `DECISIONNODE_API_KEY`, `DECISIONNODE_BASE_URL` and
`DECISIONNODE_MODEL`, and sends no telemetry.

## Install

| Language | Install | Import |
|---|---|---|
| Python 3.10+ | `pip install bynn-decisionnode` or `uv add bynn-decisionnode` | `decisionnode` |
| TypeScript, JavaScript (Node 20+, Deno, Bun, edge) | `npm install @bynn/decisionnode` | `@bynn/decisionnode` |
| Go | `go get github.com/Bynn-Intelligence/decisionnode-go` | `decisionnode` |
| Java, Kotlin (JVM 17+) | Maven `com.bynn:decisionnode` | `com.bynn.decisionnode` |
| C#, .NET 8+ | `dotnet add package Bynn.DecisionNode` | `Bynn.DecisionNode` |
| Ruby 3.2+ | `gem install bynn-decisionnode` | `decisionnode` |
| PHP 8.2+ | `composer require bynn/decisionnode` | `Bynn\DecisionNode` |
| Rust | `cargo add bynn-decisionnode` | `decisionnode` |

## The client

`DecisionNode(api_key, base_url, model, timeout, max_retries, headers, http_client)`,
every argument optional. Create one client and share it: it is safe across threads
and tasks and reuses connections.

- An empty `api_key`, `base_url` or `model` counts as not given: the environment,
  then the default, applies.
- `base_url` must be `https`. Plain `http` is accepted only for `localhost`,
  `127.0.0.1` and `::1`; anything else is an argument error before any request, so
  the key never travels unencrypted.
- `timeout` (default 10 s) covers the whole attempt, from sending to the last byte
  of the body. It must be above 0, and `max_retries` (default 2) 0 or more;
  anything else is an argument error.
- Redirects are never followed, also with your own `http_client`: the SDK wraps or
  copies it so a 3xx comes back as an error and the key is never sent to another
  URL.

Argument problems raise the language's own argument error (`ValueError`,
`ArgumentException`, `IllegalArgumentException`, `InvalidArgumentException`,
`ArgumentError`, a Go error value, a Rust `Error`), not a DecisionNode error class.

| Method | Does |
|---|---|
| `decide(state, questions, images, model)` | One request, any number of questions. Returns a `Decision`. |
| `decide_many(requests, concurrency)` | Many requests, `concurrency` at a time (default 8). One result per request in input order: a `Decision` or the error it ended with. One failure does not stop the others. |
| `check(state, instructions, ...)` | One `truth` question. Returns a `TruthAnswer`. |
| `classify(state, instructions, options)` | One `choice` question. Returns a `ChoiceAnswer`. |
| `score(state, instructions, levels)` | One `score` question. Returns a `ScoreAnswer`. |
| `gate(action, context)` | Three fixed questions about an action an agent wants to take: a risk score, whether it touches production, and allow, confirm or block. |
| `models()` | The models the key may use, with their limits. Free. |
| `decide_raw(body)` | Sends the body as given and returns the parsed JSON, for API fields newer than the SDK. |

Builders: `truth(instructions, ...)`, `choice(instructions, options)`,
`score(instructions, levels)`. A plain map in the wire form works wherever a
builder does. `options` is a map of name to description or a list of names.

A `Decision` has `answers` (by question id, also `decision[id]`), `model`,
`usage.input_tokens`, `usage.output_tokens`, `request_id`, `latency_ms`, `safety`
and `raw`. A missing `latency_ms` or token count is the language's empty value
(`None`, `null`, `nil`), never 0.

Each answer is a `TruthAnswer`, `ChoiceAnswer` or `ScoreAnswer`. An answer of a
type the SDK does not know, or of a known type with missing or wrongly typed
fields, comes back as an `UnknownAnswer` holding the raw fields; the decision
itself does not fail. Check the answer's type before reading its value.

Images: `Image(id, path)`, `Image(id, data, media_type)` or `Image(id, url)`. A file
is read when the `Image` is made, so an unreadable file fails there. When bytes or
a file come without a media type, the SDK detects JPEG, PNG or WebP from the first
bytes; any other format is an argument error.

Spelling per language:

| Neutral | Python, Ruby, Rust | TypeScript, Java, Kotlin, PHP | Go, C# |
|---|---|---|---|
| Client | `DecisionNode` | `DecisionNode` | `decisionnode.Client`, `DecisionNodeClient` |
| `decide_many` | `decide_many` | `decideMany` | `DecideMany` |
| `truth(...)` | `truth(...)` | `truth(...)` | `Truth(...)` |

Python has a sync and an async client, .NET has `Async` methods with cancellation,
and Go takes a `context.Context` first. Where `true` and `false` cannot be argument
names, the truth criteria are `if_true` and `if_false` or the language's
equivalent. Check the SDK's own README for the exact signature.

## Python

```python
from decisionnode import DecisionNode, truth, choice, score

dn = DecisionNode()

d = dn.decide(
    state={"ticket": ticket_text},
    questions={
        "route": choice("Where should this go?", {"billing": "money", "bug": "broken", "other": None}),
        "urgency": score("How urgent is this?", ["routine", "today", "urgent", "critical"]),
        "refund": truth("Is the customer asking for a refund?"),
    },
)

d["route"].choice          # "billing"
d["route"].probabilities   # {"billing": 0.87, "bug": 0.08, "other": 0.05}
d["urgency"].score         # 2.31
d["refund"].truth          # 0.94
```

Many records:

```python
results = dn.decide_many(
    [{"state": t, "questions": {"spam": truth("Is this message spam?")}} for t in messages],
    concurrency=8,
)
for msg, r in zip(messages, results):
    if isinstance(r, Exception):
        log_failure(msg, r)
    elif r["spam"].truth > 0.9:
        quarantine(msg)
```

## TypeScript

```ts
import { DecisionNode, truth, choice, score } from "@bynn/decisionnode";

const dn = new DecisionNode();

const d = await dn.decide({
  state: { ticket: ticketText },
  questions: {
    route: choice("Where should this go?", { billing: "money", bug: "broken", other: null }),
    escalate: truth("Escalate to a human now?"),
  },
});

d.answers.route.choice;    // "billing" | "bug" | "other"
d.answers.escalate.truth;  // 0.94
```

## What the SDKs leave to you

No thresholds, no caching, no deduplication, no streaming. Values arrive exactly as
the API sent them. The SDK checks almost nothing before sending; the server judges
the request, because limits depend on the model.
