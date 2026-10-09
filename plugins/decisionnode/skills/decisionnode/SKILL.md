---
name: decisionnode
description: >-
  Integrate DecisionNode, the API for fast, calibrated narrow decisions: a
  yes-or-no probability (truth), one option of a set (choice), a place on an
  ordered scale (score), a value on a grid (number), or a point or box in an
  image. Covers picking the question type, writing the state and the questions,
  reading probabilities and confidence, asking several questions in one decide
  call, decide_many, batches and sessions, images (up to 16), videos sent as
  frames, boosters (specialist readings of images, such as age and
  AI-generated, returned as evidence), fine-tuned model names, errors and
  retries, the SDKs (Python, TypeScript, Go, Java, C#, Ruby, PHP, Rust), the dn
  CLI and the docs MCP server. Use when code or an agent needs to classify,
  route, triage, check, verify, gate, count, locate or rate text, images or
  video, or when working with DECISIONNODE_API_KEY or api.decisionnode.com.
allowed-tools: Bash(dn:*), Bash(claude:*), Bash(curl:*)
compatibility: Linux, macOS, Windows
metadata:
  author: bynn
  version: "0.2.6"
license: MIT
---

# DecisionNode

DecisionNode answers narrow questions about a piece of context, fast, with a
calibrated number. It does not write text, plan or call tools. It is the part of
a system that turns "is this a refund request", "which team owns this ticket",
"how many items are on the receipt" or "where is the damaged package" into a value
code can branch on.

```
POST https://api.decisionnode.com/v1/decide     the decision call
GET  https://api.decisionnode.com/v1/models     the models a key may use, with their limits
POST https://api.decisionnode.com/v1/uploads    put large images once, name them by upload_id
POST https://api.decisionnode.com/v1/batches    batch jobs: lower price, results within 24 hours
POST https://api.decisionnode.com/v1/sessions   streaming decisions over a WebSocket
```

Authentication is `Authorization: Bearer $DECISIONNODE_API_KEY` (keys start with
`dn_live_`). Never hard-code the key, print it, or commit it, and never send it
from a browser or a mobile app: call DecisionNode from your server.

## Pick the question type

| Type | Use it for | Answer |
|---|---|---|
| `truth` | Yes or no. A question or a statement to judge. | `truth`: the probability that the answer is yes |
| `choice` | Exactly one of a set of options you define (1 to 255) | `choice` (the option name), `confidence`, `probabilities` by option name |
| `score` | A degree on an ordered scale you define, lowest first (1 to 10 levels) | `score` (expected level index), `confidence`, `probabilities` by level index, `legend` |
| `number` | A value on a grid you set: a count, a year, an age, a rating (`min`, `max`, `step`; default 0 to 255 by 1) | `number` (the most probable value), `expected`, `confidence`, `probabilities` by value |
| `point` | One spot in an image ("point to the yellow package") | `x`, `y`, `present`, `confidence`, `image`, `width`, `height` |
| `box` | A rectangle around something in an image | `x1`, `y1`, `x2`, `y2`, `present`, `confidence`, `image`, `width`, `height` |

Rules of thumb:

- Two outcomes: `truth`. Three or more categories: `choice`. Ordered intensity
  (severity, urgency, quality): `score`, not `choice`, so "a bit urgent" and "very
  urgent" stay neighbours. A quantity: `number`, not `choice` over digits.
- A `choice` always picks one of your options, even when none fits. Add an escape
  option such as `"none": "none of these apply"` when that can happen.
- `point` and `box` need an image in the request, and an `image` field naming it
  when the request has two or more. `present` says how likely the thing is there at
  all; read it before trusting the place.
- Several independent things to know about one input: several questions in one
  request, not one compound question.

## Write the state and the questions

The model sees the `state`, the `instructions`, the `criteria`, the images, the
videos and the readings of any boosters. Nothing else: not the conversation, not
the question id, not your code.

- **Put everything needed in `state`.** A string, or any JSON object or array (keys
  are seen by the model, so name them well: `ticket`, `order`, `policy`). It may be
  left out for a question that stands on its own.
- **One narrow thing per question.** "Is the customer asking for a refund?" beats
  "Is this a refund request and is the customer angry?".
- **Say what yes and no mean** when it is not obvious, with the `truth` criteria
  (`if_true` / `if_false` in the SDKs).
- **Describe options and levels** when names alone are ambiguous:
  `{"billing": "payments, invoices, refunds", "bug": "something is broken"}`.
- **The question id is only for your code.** It is returned as the answer key and
  never shown to the model, so `instructions` must carry the full meaning.
- **With two or more images, say which one** each question is about: by id in
  backticks (`` `receipt` ``), or by number from 1 in array order ("image 2").

Details and patterns: [reference/questions.md](reference/questions.md).

## Read the answer

- `truth` is a probability. 0.5 means the model cannot tell, not "half true".
  Choose the threshold in your code for what a wrong yes and a wrong no cost you,
  and send the uncertain middle to a person or a second check.
- `confidence` (choice, score, number) runs from 0 (no better than a uniform guess)
  to 1 (certain). Low confidence usually means the state does not say enough.
- `score` is the expected level index, so 2.31 on four levels sits between level 2
  and level 3. `number` is the most probable grid value and `expected` the
  probability-weighted mean. Use `probabilities` when you need the full spread.
- `point` and `box` are in pixels of the image as sent, from its top-left corner
  (`units: "normalized"` gives fractions of the width and height).
- Read answers by id, never by position, and read `probabilities` by key: their
  order is not guaranteed.
- Use the values as received. A list may sum to 0.99 or 1.01 and an entry may
  print as `0.8200000000000001`. Do not round or renormalise before comparing.
- The same request to the same pinned model returns the same answer.

## Several questions, many states

| Need | Use | Cost |
|---|---|---|
| Several questions about one state | One `decide` with several questions | One request, the state counted once |
| The same questions about many states, now | `decide_many` (SDK) or `dn batch run --live` | One request per state, run concurrently (default 8) |
| Many states, results within 24 hours | The Batch API: `run_batch` (SDK) or `dn batch run` | A lower price than live calls |
| A stream of observations against a fixed prefix (a control loop) | A session: `open_session` (SDK) or `dn session` | The prefix once, then each frame |

Questions in one request are independent: an answer never depends on the other
questions or their order. One answer is never input to another inside a request; a
follow-up that depends on an answer is a second request your code builds.

## Images and videos

Up to 16 images per request, JPEG, PNG or WebP, 10 MB each, within the model's
token limit. Send an `https` `url` when you can (nothing is uploaded); otherwise
base64 `data` with a `media_type`, or an `upload_id` from `POST /v1/uploads`
(valid for one hour). The SDKs choose for you: local images go inline when they
total under 512 KiB in a request, and are uploaded at or above it. A request body
is at most 25 MiB (26,214,400 bytes): inline base64 counts toward it, uploads and
URLs do not, and the SDKs refuse a larger body before sending it
(`RequestTooLargeError`). Each image has
an `id` that the state or the instructions can refer to. Every question sees every
image. DecisionNode reads text, amounts and layout in images, and answers through
the question types; it does not return free text, so for open-ended reading use
OCR first.

Videos are sent as frames with their times (`{"t": 0.5, "media_type", "data"}`),
up to 4 videos and 128 frames per request, read as one video with order and time.
Video files and URLs are not taken: the `dn` CLI (`--video PATH`) turns a local
file into frames on your machine.

## Boosters

A booster is a specialist model that reads the request's images before the
decision. Its reading is added to what the model sees and comes back in the
response as `evidence`. Boosters never answer or add a question.

| Booster | Reads | Returns per image |
|---|---|---|
| `age` | A picture of a person (the largest face) | `age_years`, `low`, `high`, `confidence`, `faces` |
| `ai_generated` | Any picture | `generated` (probability), `confidence`, `method` (`inference` or `c2pa`), `top_generator` (null unless likely generated), `c2pa_signer`, and `c2pa: "untrusted"` when the file's Content Credentials are not trusted |

```json
"boosters": ["age", "ai_generated"]
```

- A plain list of names is the normal form: up to 4 per request, each once.
- A booster that needs an option is an object with its `name`:
  `"boosters": ["age", { "name": "ai_generated", "images": ["poster"], "require": true }]`.
  `images` limits the booster to some of the request's images, and `require: true`
  fails the request with the 529 `booster_unavailable` when that booster fails or
  times out. Without `require`, the decision runs without that reading and
  `evidence` says why.
- The response adds `evidence` (per booster: `version`, `status` of `ok`, `timeout`,
  `error` or `skipped`, `latency_ms`, `billed_calls`, `results`), `usage.booster_tokens` and
  `usage.boosters` (the calls billed), and the header
  `x-decisionnode-boosters: age=ok:212,ai_generated=timeout:800`.
- A price per booster call billed (one per booster and image read with status
  `ok`); a timed-out or failed call is free, and a refused request pays nothing for
  its boosters. The current prices are on the pricing page:
  `https://decisionnode.com/docs/pricing`.
- `POST /v1/decide` and batch lines take boosters; sessions do not.

Details: [reference/questions.md](reference/questions.md#boosters).

## Errors and retries

The SDKs retry 408, 429, 500 to 599 (529 included), timeouts and connection errors
twice, honouring `retry-after-ms` and `Retry-After` up to 60 s. The 10 s timeout
covers the whole attempt. A decision changes nothing on the server, so a retry is
always safe. 400, 401, 402, 403, 404, 413 and 422 are never retried: fix the request.
The `x-decisionnode-error` header (`reason` in the SDKs and the CLI) says in words
what is wrong. A 403 is either a refusal under the usage policy (`RefusalError`),
which repeats if resent, or a `PermissionDeniedError` (a booster turned off for
the workspace, a suspended workspace). A required booster that failed is a 529
`booster_unavailable`, retried like any 529. The SDKs never follow a redirect and
refuse a plain `http` base URL other than loopback, so the key never leaves over an
unencrypted or unexpected connection. Full table:
[reference/errors.md](reference/errors.md).

## Models

`decisionnode-latest` is the default. `decisionnode-flash-latest` is faster and
cheaper. Pin a version (`decisionnode-1.0`, `decisionnode-1.0-flash`) when answers
must not move under you. Each model's limits (tokens per request, images and more)
are published at `GET /v1/models`; check them there instead of hard-coding them.

When `decisionnode-1.0` has no worker ready at once, the API answers from
`decisionnode-1.0-flash` instead of making you wait: the body's `model` is the
model that answered, and the headers `x-decisionnode-fallback` and
`x-decisionnode-requested-model` name the two (`decision.fallback` in the SDKs).
It is billed at Flash's price. Send `"fallback": false` (the SDKs' `fallback`
option) to get the 529 with `Retry-After` instead; the SDKs retry it. Only live
`decide` calls for `decisionnode-1.0` fall back: Flash, fine-tuned models,
sessions and batch lines never do.

A workspace can train a **fine-tuned model** on decisions it has labelled, in the
console. Call it by name in `model`, with a key of that workspace:
`decisionnode-1.0-flash@acme/fraud` (the version deployed now) or
`decisionnode-1.0-flash@acme/fraud:3` (a pinned version). The response's `model`
is always the pinned name, so you can log which version answered. Another
workspace's model, or a version that is not deployed, is the 400
`Unknown model: <name>`. `GET /v1/models` lists the workspace's fine-tuned models
with `fine_tuned`, `base`, `adapter_version` and `status`.

## Pick the integration

| Situation | Use | Reference |
|---|---|---|
| Application code | The SDK for the language | [reference/sdks.md](reference/sdks.md) |
| Shell scripts, CI checks, files of records | The `dn` CLI | [reference/cli.md](reference/cli.md) |
| A language without an SDK | Plain HTTP, the wire form in [reference/questions.md](reference/questions.md) | |
| Looking something up in the docs while you write the integration | The docs MCP server | [reference/mcp.md](reference/mcp.md) |

The MCP server reads the documentation; it does not make decisions. Decisions are
made by your code, through the API, an SDK or `dn`.

Configuration is the same everywhere:

| Setting | Environment variable | Default |
|---|---|---|
| API key | `DECISIONNODE_API_KEY` | none |
| Base URL | `DECISIONNODE_BASE_URL` | `https://api.decisionnode.com` |
| Model | `DECISIONNODE_MODEL` | `decisionnode-latest` |

An explicit argument or flag wins over the environment, which wins over the default.

## Quick example

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

if d["escalate"].truth >= 0.8:
    hand_to_human(d["route"].choice)
```

## Do not

- Do not ask DecisionNode to write, summarise or extract free text. Use it for the
  decision, and a generative model or OCR for the text.
- Do not pack two questions into one, or chain answers inside one request.
- Do not assume a fixed answer order or round the probabilities before comparing.
- Do not retry a 4xx unchanged, and never retry a refusal.
- Do not treat a booster's reading as the decision: ask the question, and read
  `evidence` only to explain or log the answer.
- Do not send the API key from a browser or a mobile app; call DecisionNode from
  your server.
