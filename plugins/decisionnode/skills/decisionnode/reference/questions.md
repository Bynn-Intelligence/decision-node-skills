# Requests, questions and answers

## The request

```json
{
  "model": "decisionnode-latest",
  "state": { "ticket": "I was charged twice and nobody has replied for 3 days." },
  "questions": {
    "route": {
      "type": "choice",
      "instructions": "Where should this go?",
      "criteria": { "billing": "money", "bug": "broken", "account": "login" }
    },
    "urgency": {
      "type": "score",
      "instructions": "How urgent is this?",
      "criteria": ["routine", "today", "urgent", "critical"]
    },
    "escalate": {
      "type": "truth",
      "instructions": "Escalate to a human now?",
      "criteria": { "true": "The customer is blocked or at risk of churning", "false": "A normal queue reply is enough" }
    }
  }
}
```

| Field | Notes |
|---|---|
| `model` | Optional. Defaults to `decisionnode-latest`. |
| `state` | A string, object or array. Objects are read with their keys. Left out or `""` when there is nothing to evaluate. |
| `questions` | A map of id to question, at least one. Any mix of types. The token limit of the model is the only bound on the count. |
| `images` | Optional, up to 4. See below. |

## Question fields

| Type | `instructions` | `criteria` |
|---|---|---|
| `truth` | What to judge. Needs `instructions` or `criteria`. | Optional: `{"true": ..., "false": ...}`, either side alone is fine |
| `choice` | What to decide | Required: `{name: description}`, 1 to 255 options. A description may be `null`. |
| `score` | What to measure | Required: a list of 1 to 10 levels, lowest first |

`instructions`, descriptions and levels may be strings or JSON. An object such as
`{"question": "...", "focus": "the last message only"}` is read as written. You
can refer to parts of the state by key in backticks, for example
`` `order.total` ``, or to an image by its id.

Option names come back byte for byte as sent: no trimming, no case folding.

## Writing good questions

- **Any phrasing works:** a question ("Does this message express urgency?"), a
  statement ("The customer is asking for a refund"; near 1 means true), a noun
  phrase ("How frustrated the customer appears"), or an imperative.
- **Narrow beats broad.** Split compound questions; they cost little extra in one
  request because the state is counted once.
- **Give the option a meaning, not just a label,** when labels overlap.
- **Escape options.** A `choice` always picks one option. Add `"none"` or
  `"other"` when the input may fit none.
- **Scales are ordered.** Write levels from lowest to highest, with comparable
  steps between them.
- **No state, no evidence.** A question asked without the facts it needs gets a
  flat answer with low confidence, not an error.

## Answers

```json
{
  "model": "decisionnode-1.0",
  "answers": {
    "route": { "type": "choice", "choice": "billing", "confidence": 0.81,
               "probabilities": { "account": 0.05, "billing": 0.87, "bug": 0.08 } },
    "urgency": { "type": "score", "score": 2.31, "confidence": 0.31,
                 "legend": { "0": "routine", "1": "today", "2": "urgent", "3": "critical" },
                 "probabilities": { "0": 0.01, "1": 0.09, "2": 0.48, "3": 0.42 } },
    "escalate": { "type": "truth", "truth": 0.94 }
  },
  "usage": { "input_tokens": 62, "output_tokens": 0 }
}
```

| Field | Meaning |
|---|---|
| `truth` | Probability of yes, 0 to 1. No confidence field: the distance from 0.5 is the confidence. |
| `choice` | The most probable option |
| `score` | Expected level index, the sum of index times probability |
| `confidence` | 0 means no better than a uniform guess, 1 means certain |
| `probabilities` | Every option or level, zeros included. Keyed by option name, or by level index as a string. |
| `legend` | Level index to the level exactly as sent |
| `model` | The resolved model version that answered |

A request succeeds for all questions or fails as a whole. There are no partial
answers. Response headers carry `x-request-id`, `x-decisionnode-model` and
`x-decisionnode-latency-ms`.

## Patterns

| Goal | Pattern |
|---|---|
| Route a ticket | `choice` over the queues, with an `other` option |
| Moderate or gate | `truth` per rule, thresholds in your code |
| Prioritise | `score` on an urgency or severity scale |
| Check a claim against a source | State `{"source": ..., "claim": ...}`, `truth` "Is the claim supported by the source?" |
| Extract a field from a fixed set | `choice` over the candidates, for example currencies |
| Verify a document image | Expected values in the state, one `truth` per field: "Does the total on the receipt equal the total in the claim?" |
| Many records | `decide_many` or `dn batch`, the same questions for every record |

## Images

```json
{
  "state": { "claim": { "total": "740.00", "currency": "SEK" } },
  "images": [ { "id": "receipt", "media_type": "image/jpeg", "data": "<base64>" } ],
  "questions": {
    "total_matches": { "type": "truth", "instructions": "Does the total on the receipt equal the total in the claim?" },
    "legible": { "type": "score", "instructions": "How readable is the receipt?",
                 "criteria": ["unreadable", "partly readable", "fully readable"] }
  }
}
```

An image is `{id, data, media_type}` (`image/jpeg`, `image/png` or `image/webp`) or
`{id, url}` with an `https` URL. Up to 4 per request, 10 MB each. Image tokens count
toward the request's token limit.
