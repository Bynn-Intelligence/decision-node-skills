---
name: decisionnode
description: >-
  Integrate DecisionNode, the API for fast, calibrated narrow decisions: a
  yes-or-no probability (truth), one option of a set (choice) or a place on an
  ordered scale (score). Covers picking the question type, writing the state and
  the questions, reading probabilities and confidence, asking several questions
  in one decide call, decide_many for many states, images, errors and retries,
  the SDKs (Python, TypeScript, Go, Java, C#, Ruby, PHP, Rust), the dn CLI and
  the MCP server. Use when code or an agent needs to classify, route, triage,
  check, verify, gate or rate text or images, or when working with
  DECISIONNODE_API_KEY, api.decisionnode.com or mcp.decisionnode.com.
allowed-tools: Bash(dn:*), Bash(claude:*), Bash(uvx:*), Bash(curl:*)
compatibility: Linux, macOS, Windows
metadata:
  author: bynn
  version: "0.1.0"
license: MIT
---

# DecisionNode

DecisionNode answers narrow questions about a piece of context, fast, with a
calibrated number. It does not write text, plan or call tools. It is the part of
a system that turns "is this a refund request", "which team owns this ticket" or
"how urgent is this" into a value code can branch on.

```
POST https://api.decisionnode.com/v1/decide
GET  https://api.decisionnode.com/v1/models
```

Authentication is `Authorization: Bearer $DECISIONNODE_API_KEY`. Never hard-code the
key, print it, or commit it.

## Pick the question type

| Type | Use it for | Answer |
|---|---|---|
| `truth` | Yes or no. A question or a statement to judge. | `{"truth": 0.94}`: the probability that the answer is yes |
| `choice` | Exactly one of a set of options you define (1 to 255) | `choice` (the option name), `confidence`, `probabilities` by option name |
| `score` | A degree on an ordered scale you define, lowest first (1 to 10 levels) | `score` (expected level index, 0 to levels minus 1), `confidence`, `probabilities` by level index, `legend` |

Rules of thumb:

- Two outcomes: `truth`. Three or more categories: `choice`. Ordered intensity
  (severity, urgency, quality): `score`, not `choice`, so "a bit urgent" and "very
  urgent" stay neighbours.
- A `choice` always picks one of your options, even when none fits. Add an escape
  option such as `"none": "none of these apply"` when that can happen.
- Several independent things to know about one input: several questions in one
  request, not one compound question.

## Write the state and the questions

The model sees the `state`, the `instructions`, the `criteria` and any images.
Nothing else: not the conversation, not the question id, not your code.

- **Put everything needed in `state`.** A string, or any JSON object or array (keys
  are seen by the model, so name them well: `ticket`, `order`, `policy`). It may be
  left out for a question that stands on its own.
- **One narrow thing per question.** "Is the customer asking for a refund?" beats
  "Is this a refund request and is the customer angry?".
- **Say what yes and no mean** when it is not obvious, with the `truth` criteria
  (`if_true` / `if_false` in the SDKs and tools).
- **Describe options and levels** when names alone are ambiguous:
  `{"billing": "payments, invoices, refunds", "bug": "something is broken"}`.
- **The question id is only for your code.** It is returned as the answer key and
  never shown to the model, so `instructions` must carry the full meaning.

Details and patterns: [reference/questions.md](reference/questions.md).

## Read the answer

- `truth` is a probability. 0.5 means the model cannot tell, not "half true".
  Choose the threshold in your code for what a wrong yes and a wrong no cost you,
  and send the uncertain middle to a person or a second check.
- `confidence` (choice and score) runs from 0 (no better than a uniform guess) to
  1 (certain). Low confidence usually means the state does not say enough.
- `score` is the expected level index, so 2.31 on four levels sits between level 2
  and level 3. Use `probabilities` when you need the full spread.
- Read answers by id, never by position, and read `probabilities` by key: their
  order is not guaranteed.
- Use the values as received. A list may sum to 0.99 or 1.01 and an entry may
  print as `0.8200000000000001`. Do not round or renormalise before comparing.
- The same request to the same pinned model returns the same answer.

## Several questions, many states

| Need | Use | Cost |
|---|---|---|
| Several questions about one state | One `decide` with several questions | One request, the state counted once |
| The same questions about many states | `decide_many` (SDK, MCP) or `dn batch` | One request per state, run concurrently (default 8) |

Questions in one request are independent: an answer never depends on the other
questions or their order. One answer is never input to another inside a request; a
follow-up that depends on an answer is a second request your code builds.

## Images

Up to 4 images per request, JPEG, PNG or WebP, 10 MB each, as base64 `data` with a
`media_type`, or an `https` `url`. Each has an `id` that the state or the
instructions can refer to. Every question sees every image. DecisionNode reads
text, amounts and layout in images, and answers through the three types: verify a
value against the state (`truth`), select among candidates (`choice`), or measure
(`score`). It does not return free text; for open-ended reading, use OCR first.

The SDKs detect the media type of a file or of bytes from the first bytes (JPEG,
PNG, WebP) when none is given. The hosted MCP server takes about 3 MiB of base64
image data per tool call; send larger images by `https` URL.

## Errors and retries

The SDKs retry 408, 429, 500 to 599 (529 included), timeouts and connection errors
twice, honouring `retry-after-ms` and `Retry-After` up to 60 s. The 10 s timeout
covers the whole attempt. A decision changes nothing on the server, so a retry is
always safe. 400, 401, 402, 403, 404 and 422 are never retried: fix the request.
The `x-decisionnode-error` header (`reason` in the SDKs, CLI and MCP) says in words
what is wrong. A 403 is either a refusal under the usage policy (`RefusalError`),
which repeats if resent, or a `PermissionDeniedError`. The SDKs never follow a
redirect and refuse a plain `http` base URL other than loopback, so the key never
leaves over an unencrypted or unexpected connection. Full table:
[reference/errors.md](reference/errors.md).

## Models

`decisionnode-latest` is the default. `decisionnode-flash-latest` is faster and
cheaper. Pin a version (`decisionnode-1.0`, `decisionnode-1.0-flash`) when answers
must not move under you. Each model's limits (tokens per request and more) are
published at `GET /v1/models`; check them there instead of hard-coding them.

## Pick the integration

| Situation | Use | Reference |
|---|---|---|
| Application code | The SDK for the language | [reference/sdks.md](reference/sdks.md) |
| Shell scripts, CI checks, files of records | The `dn` CLI | [reference/cli.md](reference/cli.md) |
| An agent deciding while it works | The MCP server | [reference/mcp.md](reference/mcp.md) |
| A language without an SDK | Plain HTTP, the wire form in [reference/questions.md](reference/questions.md) | |

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
- Do not send the API key from a browser or a mobile app; call DecisionNode from
  your server.
