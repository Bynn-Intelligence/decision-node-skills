# SDKs

Every SDK has the same surface and the same behaviour; only the spelling follows
the language. Each reads `DECISIONNODE_API_KEY`, `DECISIONNODE_BASE_URL` and
`DECISIONNODE_MODEL`, sends no telemetry, and exports the version of the SDK
specification it implements as `SPEC_VERSION` (`SpecVersion` in Go and C#). This
page describes specification 1.3: boosters and fine-tuned model names.

## Install

| Language | Install | Import |
|---|---|---|
| Python 3.10+ | `pip install bynn-decisionnode` or `uv add bynn-decisionnode` | `decisionnode` |
| TypeScript, JavaScript (Node 20+, Deno, Bun, edge) | `npm install @bynn/decisionnode` | `@bynn/decisionnode` |
| Go | `go get github.com/Bynn-Intelligence/decision-node-go` | `github.com/Bynn-Intelligence/decision-node-go` (package `decisionnode`) |
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
| `decide(state, questions, images, videos, model, boosters)` | One request, any number of questions. Returns a `Decision`. |
| `decide_many(requests, concurrency)` | Many requests, `concurrency` at a time (default 8). One result per request in input order: a `Decision` or the error it ended with. One failure does not stop the others. |
| `check(state, instructions, ...)` | One `truth` question. Returns a `TruthAnswer`. |
| `classify(state, instructions, options)` | One `choice` question. Returns a `ChoiceAnswer`. |
| `score(state, instructions, levels)` | One `score` question. Returns a `ScoreAnswer`. |
| `number(state, instructions, min, max, step)` | One `number` question. Returns a `NumberAnswer`. |
| `gate(action, context)` | Three fixed questions about an action an agent wants to take: a risk score, whether it touches production, and allow, confirm or block. |
| `models()` | The models the key may use, with their limits. Free. |
| `upload(images)` | Uploads images (`POST /v1/uploads`) and returns one `upload_id` each, valid for one hour. |
| `open_session(...)` | Opens a session for streaming decisions; `Session.send`, `replies` and `end`, and `supervise` for a feed that reopens on its own. |
| `batches.create`, `add`, `finalize`, `get`, `list`, `results`, `cancel`, and `run_batch(requests)` | The Batch API: a lower price, results within 24 hours. `run_batch` creates, adds, finalizes, polls and returns the results. |
| `check_request(method, request)` | Runs every local check a call would run, sends nothing. |
| `decide_raw(body)` | Sends the body as given and returns the parsed JSON, for API fields newer than the SDK. |

The helpers (`check`, `classify`, `score`, `number`, `gate`) take `images`,
`videos`, `model` and `boosters` like `decide`.

Builders: `truth(instructions, ...)`, `choice(instructions, options)`,
`score(instructions, levels)`, `number(instructions, min, max, step)`,
`point(instructions, image, units)`, `box(instructions, image, units)`. A plain map
in the wire form works wherever a builder does. `options` is a map of name to
description or a list of names.

A `Decision` has `answers` (by question id, also `decision[id]`), `model`,
`usage.input_tokens`, `usage.output_tokens`, `request_id`, `latency_ms`, `safety`
and `raw`; with videos also `usage.video_frames`, `usage.video_seconds` and
`warnings`; with boosters also `evidence`, `usage.booster_tokens` and
`usage.boosters`. A value the response does not carry is the language's empty value
(`None`, `null`, `nil`), never 0.

Each answer is a `TruthAnswer`, `ChoiceAnswer`, `ScoreAnswer`, `NumberAnswer`,
`PointAnswer` or `BoxAnswer`. An answer of a type the SDK does not know, or of a
known type with missing or wrongly typed fields, comes back as an `UnknownAnswer`
holding the raw fields; the decision itself does not fail. Check the answer's type
before reading its value.

Images: `Image(id, url)` (recommended: nothing is uploaded), `Image(id, path)`,
`Image(id, data, media_type)` or `Image(id, upload_id)`. Up to 16 a request. When
bytes or a file come without a media type, the SDK detects JPEG, PNG or WebP from
the first bytes. Local images go inline as base64 when they total under 512 KiB in
a request (`DEFAULT_INLINE_THRESHOLD`; the client's `inline_threshold` overrides
it) and are uploaded at or above it; an image uploaded before is sent by its cached
`upload_id`. No image is ever resized or re-encoded.

Videos: `Video(id, frames, fps, start, end)` with each frame a
`VideoFrame(t, data, media_type)`. Up to 4 videos a request. The SDKs do not turn
a video file into frames; the `dn` CLI does.

The SDK checks the API's fixed rules before sending (question shapes, option and
level counts, number grids, image types and sizes, more than 16 images or 4
videos) and raises the API's own error class, so a request the server would refuse
for those reasons never leaves. Token limits, boosters and model names stay the
server's to judge.

## Boosters

`boosters` is a list in the caller's order; a plain list of names
(`["age", "ai_generated"]`) is the normal form. An entry is a booster name or, for
a booster that needs an option, `Booster(name, images, require, options)`, sent as
`{"name": name, "images"?, "require"?, "options"?}` with each argument left out
when not given; a `Booster` with no option set is sent as the bare name. Left out
or empty, the request carries no `boosters` key. Names are
strings, not a closed set, so a booster added on the server works with an older
SDK; TypeScript types them as `"age" | "ai_generated" | (string & {})`.

`decision.evidence` maps each booster's name, in the request's order, to an
`Evidence` with `version`, `status` (`ok`, `timeout`, `error`, `skipped`, or any
other value as received), `latency_ms`, `billed_calls` (the calls of that booster
billed on the request) and `results`. Each result is an
`AgeReading` (`image`, `faces`, `age_years`, `low`, `high`, `confidence`; the age
fields empty when `faces` is 0) or an `AiGeneratedReading` (`image`, `generated`,
`confidence`, `method`, `top_generator` with `name` and `probability` or empty
when the picture does not read as likely generated, `c2pa_signer`, and `c2pa`,
which is `"untrusted"` for Content Credentials that are not trusted and empty
otherwise). A reading of a booster the SDK does not know, or one with a field
missing or of the wrong type, is a generic reading holding its raw fields, and the
decision does not fail. So are the entries of pictures a booster did not read
(`{"image": id}` under a `timeout` or `error` status) or could not decode
(`{"image": id, "readable": false}`). Fields the SDK does not know are ignored.

Every error of a request that named boosters carries `boosters`: the
`x-decisionnode-boosters` header parsed into booster name to `status` and
`latency_ms`, so you can see which required booster failed. A 403
`booster_not_enabled` is a `PermissionDeniedError`; a 529 `booster_unavailable`
is an `OverloadedError`, retried as every 529.

## Fallback

`decide`, the helpers, `decide_many`'s requests and batch lines take `fallback`
(a boolean), sent only when given. `decision.fallback` is empty on an ordinary
answer, and holds `served_model` (the pinned id that answered) and
`requested_model` (what was asked: the family id, or the pinned id if one was sent) when a
`decisionnode-moe` request was answered by Flash because no worker of it was ready;
`decision.model` is the model that answered. With `fallback=False` such a
request is a 529, an `OverloadedError` retried like any 529.

## Fine-tuned models

`model` is free text: a fine-tuned model's name (`decisionnode-flash@acme/fraud`
or the pinned `decisionnode-flash@acme/fraud:3`) is sent as given and never
checked locally, on a call or as the client's `model`. `decision.model` is the
pinned name the server answered with. An unknown or another workspace's name is the
server's 400 `Unknown model: <name>`, a `BadRequestError`. `models()` entries carry
`fine_tuned`, `base`, `adapter_version` and `status` for the workspace's
fine-tuned models, and none of them for the catalogue's. Training and deploying a
fine-tuned model is done in the console; the SDKs have no training method.

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

Boosters:

```python
from decisionnode import Booster, Image, truth

d = dn.decide(
    images=[Image("person", url=person_url), Image("poster", url=poster_url)],
    questions={
        "adult": truth("Is the person in the first picture an adult?"),
        "synthetic": truth("Is the second picture AI-generated?"),
    },
    boosters=["age", "ai_generated"],
)

d["adult"].truth                          # 0.97
d.evidence["age"].results[0].age_years    # 27
d.usage.boosters                          # booster calls billed

# A booster that needs an option: only the poster, and fail if it cannot be read.
boosters = ["age", Booster("ai_generated", images=["poster"], require=True)]
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

No thresholds, no deduplication, no streaming outside sessions, and no caching
except of image uploads by content hash for the upload's hour. Values arrive
exactly as the API sent them.
