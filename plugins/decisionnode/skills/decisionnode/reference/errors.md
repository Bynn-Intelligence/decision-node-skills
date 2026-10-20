# Errors, retries and the safety check

## Retries

Built into every SDK and the CLI:

- 10 seconds per attempt, covering the whole attempt from sending to the last
  byte of the body. 2 retries after the first attempt.
- Retried: 408, 429, every 500 to 599 (529 included, `booster_unavailable` too),
  timeouts, connection errors. Not the knowledge 529 with `details.reason`
  `ingestion_delayed`: documents have waited over 15 minutes to be read, so the caller
  decides.
- Wait: `retry-after-ms` when sent, else `Retry-After` (seconds or an HTTP date),
  capped at 60 s; else exponential backoff from 0.5 s with jitter, capped at 8 s.
- Never retried: 400, 401, 402, 403, 404, 413, 422. Resending them unchanged gives
  the same error.

Do not wrap an SDK call in a second retry loop. If you run many requests, keep
concurrency modest (8 is the default) and let 429s slow you down.

## Error classes

All derive from `DecisionNodeError` with `status`, `error_type`, `message`,
`request_id`, `reason` and `boosters`. `message` is the server's `message` (an
empty string when the server sent none, never null), or the client's description
when there was no response. `reason` comes from the `x-decisionnode-error` header
and says what is wrong in words, for example
`question 'q': a score takes up to 10 levels, got 11`. Show it, or use it to fix
the request. `boosters` is the `x-decisionnode-boosters` header parsed: each
booster's name to its `status` and `latency_ms`, in the request's order, empty when
the request named none.

Only 200 to 299 is success. Redirects are never followed: a 3xx, like any other
status without a row below, is the base `DecisionNodeError` with its `status`. A
2xx body that is not JSON is a `ServerError`. Problems with the arguments (an
`http` base URL other than loopback, a `timeout` of 0, an empty question map)
raise the language's own argument error before anything is sent. A fault in the
request's content that the API's fixed rules catch (an image of an unknown format,
too many options or levels, a malformed number grid) raises the API's own error
class locally, before any request.

| Status | Error | What to do |
|---|---|---|
| 400 | `BadRequestError` | Fix the request: unknown model, too many options or levels, a bad image |
| 400, `max_tokens_exceeded` | `ContextLimitError` | Shorten the state, send fewer or smaller images, or split the questions; the reason gives the count and the limit |
| 400, `booster_unknown` | `BadRequestError` | A name that is not a booster. Check the spelling. |
| 400, `booster_input_mismatch` | `BadRequestError` | A booster that reads images on a request without one, or an `images` entry that is not an image of the request |
| 400, `api_usage_error` on `boosters` | `BadRequestError` | The list is malformed: more than 4, a booster named twice, an entry that is neither a name nor an object with `name`, a key of the object other than `name`, `images`, `require` and `options`, a key in `options`. The reason says which. |
| 400, `collection_type_mismatch` | `BadRequestError` | `knowledge` or a search naming a face collection, `face_recognition` a knowledge base, or a document sent to a face collection |
| 400, `upload_expired`, `upload_consumed`, `upload_not_found`, `upload_incomplete` | `BadRequestError` | A document's `upload_id` is stale. The SDKs upload a file they placed themselves again, once; upload again yourself for an id you gave. |
| 400, `upload_purpose_mismatch` | `BadRequestError` | An image upload named as a document, or a knowledge upload named as an image. Upload with the right purpose. |
| 401 | `AuthenticationError` | Key missing or wrong. Check `DECISIONNODE_API_KEY`. |
| 402 | `InsufficientCreditError` | The prepaid balance is empty. Send again only after credit is added. |
| 403, `refusal_error` | `RefusalError` (`category`: `harm` or `self_harm`) | Refused under the usage policy. Do not retry. |
| 403, any other | `PermissionDeniedError` | Not allowed: `booster_not_enabled` (the booster is turned off for the workspace), `workspace_suspended`, `key_scope_denied` (a search, `include_text` or a knowledge upload from a key that is not full-scope). Do not retry. |
| 404 | `NotFoundError` | Wrong path or base URL; `collection_not_found`, `item_not_found` for an id that is not this workspace's |
| 409 | `DecisionNodeError` (`status` 409, `error_type`, `details`) | `knowledge_collection_empty` (`require: true` on a knowledge base with no document ready or on its way; `details.items`, `details.failed`), `reference_taken` (`details.item_id`), `pinned_budget_exceeded` (the pins are over the knowledge base's cap), `chunks_limit_reached`, `items_limit_reached`, `collections_limit_reached`. Fix the cause; not retried. |
| 413, or over 26,214,400 bytes before sending | `RequestTooLargeError` | The body is over 25 MiB. Send large images as uploads (`POST /v1/uploads`) or by URL. The SDKs check the encoded body before sending and raise this locally, sending nothing. With `error_type` `item_too_large`: a document's text is over 512 KiB once normalised; split it. |
| 422 | `ValidationError` (`entries`) | A field is missing or of the wrong type, or a list is too long (more than 16 images, more than 4 videos); `entries` lists each one. `invalid_text`: a document that is not UTF-8 or holds a NUL. |
| 429 | `RateLimitError` (`retry_after`, `details`) | Retried automatically; raised only after the retries. Document writes have their own rate per workspace (`details.reason` `ingest_queue_full` or `ingest_tokens_per_hour`). |
| 529 | `OverloadedError` (`retry_after`) | Retried automatically. With `error_type` `booster_unavailable`, a booster with `require: true` failed or timed out, or a required `knowledge` reading found no document ready yet (`Retry-After: 5`); `boosters` shows which. With `details.reason` `ingestion_delayed` (`Retry-After: 60`) it is raised at once. |
| other 5xx | `ServerError` | Retried automatically |
| none | `ConnectionError`, `TimeoutError` | Retried automatically |

In Go, errors are values matched with `errors.As`. Every request id is in
`x-request-id`; include it when you contact support.

The SDK checks nothing about boosters before sending: the API judges the list, the
names and which boosters the workspace may use, before any booster runs and before
any charge. A model name is never checked locally either: an unknown name, or a
fine-tuned model of another workspace, is the API's 400 `Unknown model: <name>`.

## The safety check

On the hosted API every decision response carries `x-decisionnode-safety`, which
the SDKs parse into `decision.safety` (`checked`, `harm`, `self_harm`, `flagged`).
Send the request header `x-decisionnode-safety-body: true` to also get it as a
`safety` field in the body. A request that asks to choose, rank or target people to
be harmed, or to help someone harm themselves, can be refused with a 403
`refusal_error`. It is never retried, and it is not billed, its boosters included.
The check judges the request as sent, never a booster's reading.

## CLI exit codes

| Code | Meaning |
|---|---|
| 0 | Answered |
| 1 | Answered, and `--min` was not met |
| 2 | Bad command line or input, or a fixed API rule checked locally; nothing was sent |
| 3 | Key missing or rejected, or out of credit (401, 402) |
| 4 | Refused by the safety check (403) |
| 5 | The API rejected the request (400, 404, 422, over the token limit) |
| 6 | Temporary failure after the retries (429, 529, other 5xx, network) |
| 7 | `dn batch` finished and some lines failed, or `dn batch run` timed out before the batch ended |
| 8 | `dn session` ended with a close code other than `1000` |
