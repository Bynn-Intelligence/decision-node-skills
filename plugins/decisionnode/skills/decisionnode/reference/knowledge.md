# Knowledge

A knowledge base holds a workspace's own documents: a claims policy, house rules, a
mission's special instructions, a robot's operating manual, the handling rules for one
vehicle model. The `knowledge` booster finds the passages that apply to a decision and
gives them to the model as facts and rules to apply; the response says which passages
the model read, with a citation for each. A knowledge base is a collection of type
`text` under `/v1/collections`, beside the face collections.

```
POST   /v1/collections                              create a knowledge base: {"type": "text", "name", "scope_key"?}
GET    /v1/collections/{id}                         the knowledge base, with its counts
POST   /v1/collections/{id}/items                   add a document (202, read in the background; ?wait=true holds up to 10 s)
GET    /v1/collections/{id}/items                   the documents, paged, never their text
GET    /v1/collections/{id}/items/{item_id}         one document; ?include=text adds its stored text
PUT    /v1/collections/{id}/items/{item_id}         replace a document whole (a new version)
PATCH  /v1/collections/{id}/items/{item_id}         reference, label, metadata, pinned, pin_rank (at once, free), title (a new version)
GET    /v1/collections/{id}/items/{item_id}/chunks  the document's searchable chunks, paged
DELETE /v1/collections/{id}/items/{item_id}         delete a document, its text and its chunks
POST   /v1/collections/{id}/search                  the passages a query finds, without a decision
DELETE /v1/collections/{id}                         delete the knowledge base and all it holds
```

## Create a knowledge base

```json
{ "type": "text", "name": "Claims policy", "scope_key": "mission" }
```

`scope_key` is optional, `^[a-z0-9_]{1,40}$`, and fixed for the collection's life. It
names the one metadata key whose value scopes a document to, say, one mission or one
site (see Scope below). Leave it out when every document applies everywhere.

The collection object adds `scope_key`, `chunks`, `tokens`, `version` (raised by every
change a search can see), `status_counts` (`queued`, `processing`, `ready`, `failed`)
and `pinned` (`tokens`, `cap`, `largest_scope`).

## Add documents

```json
{ "title": "Claims policy 2026", "text": "# Receipts\n\nReject any claim over 500 SEK without a receipt.",
  "format": "markdown", "reference": "policy-2026", "pinned": true }
```

| Field | Notes |
|---|---|
| `title` | Required, 1 to 200 characters. Part of what is searched. |
| `text` | Markdown (`format` `markdown`, the default) or plain text (`format` `text`), UTF-8 without NUL, at most 512 KiB once normalised. Markdown is cut by its headings, so give a policy real headings. |
| `reference` | Optional, `[A-Za-z0-9_.:-]{1,64}`, unique in the knowledge base. Your own id for the document; left out, the item's id is used. |
| `pinned`, `pin_rank` | `true`: always given to a decision that names the knowledge base (below). `pin_rank` 0 to 1,000 orders the pins, lowest first. |
| `label`, `metadata` | A label, and metadata to match and filter on. On a scoped knowledge base the scope key's value in `metadata` scopes the document; without it the document is global. |

Files: text, Markdown, PDF, DOCX, PPTX, XLSX, HTML and images (PNG, JPEG, TIFF, WebP),
at most 50 MB and 100 pages for a PDF. A file is converted to text, and only its text
is kept once it is ready: the original is deleted. 512 KiB of text applies after
conversion. A file goes up through `POST /v1/uploads` with `"purpose": "knowledge"` (a
full-scope key) and the item names its `upload_id`; the SDKs and `dn` do all of it from a
path, sending a small text or Markdown file inline instead.

Reading is asynchronous. An item answers `202` `queued`, then is `processing` (`stage`
`extracting` for a file, `chunking`, `embedding`), then `ready` or `failed` (`error`
says why; a document whose new version fails keeps its previous version serving).
`?wait=true` holds the call up to 10 s and answers once ready, else as it stands; the
SDKs' `wait_until_ready` polls until a document, or the whole knowledge base, is done.
`warnings` may flag `possible_secret` or `possible_instruction` in a document; they are
shown, never refused.

## Pinned documents and scope

- **Pin a rule that must always apply.** Search finds the passages that look relevant
  to the request; a pinned document is given every time, whatever the query, never
  subject to `top_k` or ranking. Keep pins short: their load per scope value is capped
  (512 tokens by default, `pinned.cap`), and a write past it is the 409
  `pinned_budget_exceeded`.
- **Scope keys for missions, sites, customers.** With `scope_key` `mission`, a
  document with `"metadata": {"mission": "M-42"}` belongs to M-42 and one without the
  key is global. A decision that names `"scope": "M-42"` reads the global documents and
  M-42's, never another mission's. Without `scope` it reads the global documents only,
  with the warning `scope_not_named`. The scope key is named only through `scope`, never
  in `match` or `filter` (a 400), so no filter can widen a scope.

## The booster

```json
{
  "model": "decisionnode-moe",
  "state": { "claim": { "amount": "740.00", "receipt": false }, "mission": "M-42" },
  "boosters": [
    { "name": "knowledge", "require": true,
      "options": { "collection": "col_3f6c1a9e0b2d4c7f8a1e5d9b2c4f6a80", "scope": "M-42", "top_k": 4 } }
  ],
  "questions": {
    "approve": { "type": "truth", "instructions": "Should the claim be approved under our policy?" }
  }
}
```

The object form only: the bare name `"knowledge"` is a 400, since `collection` is
required. The booster reads the request's state and questions, never a picture:
`images` on it is the 400 `booster_input_mismatch`. One knowledge base a request; it
counts as one of the 4 boosters and runs beside image boosters. Batch lines take it;
sessions take no boosters.

| Option | Default | |
|---|---|---|
| `collection` | required | The knowledge base's `col_` id. A face collection is the 400 `collection_type_mismatch`; another workspace's id is the 404 `collection_not_found`. |
| `query` | built from the request | Every question's `instructions`, then the state as `path: value` lines. Give `query` (1 to 2,000 characters) when the request's wording would search badly. |
| `scope` | none | The value of the scope key (1 to 500 characters); on a knowledge base without one, a 400. |
| `match` | none | Metadata equality: `{"region": "SE", "product": ["car", "home"]}` (an array is any of). |
| `filter` | none | A typed tree: `{"and": [...]}`, `{"or": [...]}`, a metadata leaf `{"key", "op", "value"}` (`eq`, `ne`, `in`, `nin`, `gt`, `gte`, `lt`, `lte`, `exists`) or an item leaf `{"attr": "reference" or "item", "op", "value"}`. |
| `top_k` | 4 | 0 to 20: the most passages found by search, pins not counted. `0` gives the pins only. |
| `max_tokens` | `"auto"` | The found passages' token budget: `auto` fits them to the room the request leaves, or an integer 128 to 8,192. |
| `pinned` | `true` | `false` leaves the pinned documents out. |
| `min_score` | none | 0 to 1: a floor for passages found by meaning alone; passages that match on words are kept. |
| `include_text` | `false` | Adds each passage's `text` and the query's text to the evidence; a full-scope key only. |

`match` and `filter` apply to pins and found passages alike, and are strict: a document
without the key does not match. A global pin a filter excludes is counted in
`omitted.pinned_filtered` with the warning `pinned_filtered`.

## Reading the passages

```json
"evidence": { "knowledge": { "version": "knowledge-v1", "status": "ok", "latency_ms": 141, "billed_calls": 1,
  "results": [ {
    "collection": "col_3f6c...", "collection_name": "Claims policy", "corpus": { "version": 41 },
    "query": { "source": "auto", "tokens": 212 },
    "budget": { "mode": "auto", "tokens": 840, "entry": "short", "cause": null },
    "scope": { "key": "mission", "value": "M-42" }, "warnings": [],
    "passages": [
      { "n": 1, "pinned": true, "item": "itm_...", "reference": "policy-2026", "title": "Claims policy 2026",
        "heading": "Receipts", "chunk": 3, "byte_start": 1840, "byte_end": 2310, "tokens": 96,
        "score": null, "lexical": false, "rendered": true } ],
    "omitted": { "below_min_score": 0, "per_item_cap": 1, "over_budget": 1, "pinned_filtered": 0, "short_entry": 0, "context_limit": 0 },
    "pending_items": 0, "search": { "plan": "exact", "candidates": 50, "fallback": false }, "truncated": false } ] } }
```

- `passages` are in the order the model read them, pinned first; `n` is the passage's
  number. `score` is the similarity, `null` for a pin. `rendered: false` marks a passage
  left out to fit the model's context (counted in `omitted`).
- **Citations**: `item` (the document's id), `reference`, `title`, `heading`, `chunk`,
  and `byte_start`, `byte_end`: UTF-8 byte offsets, end exclusive, into the document's
  stored text (`GET .../items/{item_id}?include=text`). Slice the UTF-8 bytes, not the
  string: in JavaScript, Java and C# encode the text to UTF-8 first.
- A publishable key's reading carries ids and offsets only: `collection_name`, `title`,
  `heading` and `reference` are `null`.
- `warnings`: `scope_not_named`, `over_budget` (a passage matched but the budget left no
  room), `budget_floor` (`require` kept the top passage anyway), `pinned_filtered`.
- `pending_items` counts documents not ready yet, which the search could not see.
- Ask the question your code acts on and read its answer; the passages are there to
  show and log why.

## `require` and the statuses

`require` guarantees that the retrieval ran over a ready knowledge base, that every pin
in scope reached the model, and that at least the top found passage did when one
matched. It does not guarantee every relevant passage: pin what must always apply.

| Reading | Without `require` | With `require: true` |
|---|---|---|
| `ok` | Given to the model, billed | The same; with no room under `auto` the top passage is kept anyway (`budget_floor`) |
| `timeout`, `error` | The decision runs without it, not billed | 529 `booster_unavailable`, retried |
| `skipped`: no document ready yet, some on their way | The decision runs without it ("no document is ready yet"), not billed | 529 `booster_unavailable` with `Retry-After: 5`, retried; queued past 15 minutes, `Retry-After: 60` and `details.reason` `ingestion_delayed`, which the SDKs raise at once |
| `skipped`: nothing ready or on its way (no documents, or all failed) | The same | 409 `knowledge_collection_empty`, `details.items`, `details.failed` |

## Search without a decision

```json
POST /v1/collections/{id}/search
{ "query": "receipts over 500 SEK", "scope": "M-42", "top_k": 4 }
```

It takes `query` (required), `scope`, `match`, `filter`, `top_k`, `pinned` and
`max_tokens`, and answers the reading above with every passage's `text` (no `rendered`,
no `truncated`). Use it to check what a knowledge base gives a query before a decision
relies on it. It needs a full-scope key and is billed as one knowledge call.

## SDKs

Specification 1.4. Python:

```python
from decisionnode import DecisionNode, Document, knowledge, truth

dn = DecisionNode()

kb = dn.collections.create("Claims policy", type="text", scope_key="mission")

# A rule that must always apply: inline Markdown, pinned.
dn.collections.add_document(
    kb["id"], "# Receipts\n\nReject any claim over 500 SEK without a receipt.",
    title="Claims policy 2026", reference="policy-2026", pinned=True,
)
# One mission's brief, from a PDF: uploaded, converted to text, scoped to M-42.
dn.collections.add_document(kb["id"], Document(path="m-42-brief.pdf"), metadata={"mission": "M-42"})
dn.collections.wait_until_ready(kb["id"])   # every document ready or failed

d = dn.decide(
    state={"claim": {"amount": "740.00", "receipt": False}, "mission": "M-42"},
    questions={"approve": truth("Should the claim be approved under our policy?")},
    boosters=[knowledge(kb["id"], scope="M-42", require=True)],
)

d["approve"].truth                                   # 0.04
reading = d.evidence["knowledge"].results[0]
for p in reading.passages:
    print(p.n, p.pinned, p.title, p.heading, p.score)

# Quote a passage from the document's stored text, by its UTF-8 byte offsets.
p = reading.passages[0]
text = dn.collections.get_item(kb["id"], p.item, include_text=True)["text"]
quote = text.encode("utf-8")[p.byte_start:p.byte_end].decode("utf-8")

hits = dn.collections.search(kb["id"], "receipts over 500 SEK", scope="M-42")
```

TypeScript:

```ts
import { DecisionNode, Document, knowledge, truth } from "@decisionnode/sdk";

const dn = new DecisionNode();

const kb = await dn.collections.create({ name: "Claims policy", type: "text", scopeKey: "mission" });
await dn.collections.addDocument(kb.id, {
  document: "# Receipts\n\nReject any claim over 500 SEK without a receipt.",
  title: "Claims policy 2026", reference: "policy-2026", pinned: true,
});
await dn.collections.addDocument(kb.id, {
  document: Document.fromPath("./m-42-brief.pdf"), metadata: { mission: "M-42" },
});
await dn.collections.waitUntilReady(kb.id);

const d = await dn.decide({
  state: { claim: { amount: "740.00", receipt: false }, mission: "M-42" },
  questions: { approve: truth("Should the claim be approved under our policy?") },
  boosters: [knowledge(kb.id, { scope: "M-42", require: true })],
});

const hits = await dn.collections.search(kb.id, { query: "receipts over 500 SEK", scope: "M-42" });
```

The other SDKs spell the same calls in their language: `collections.create(name,
type, scope_key)`, `add_document`, `replace_document`, `update_item` (with `pinned`,
`pin_rank`, `title`), `get_item(include_text)`, `list_items`, `list_chunks`,
`delete_item`, `wait_until_ready(collection_id, item_id, timeout, poll_interval)`,
`search`, `upload_documents` (upload 1 to 16 files ahead of time, for a later
`Document(upload_id)`), and the builder `knowledge(collection, query, scope, match,
filter, top_k, max_tokens, pinned, min_score, include_text, require)`. The reading is a
`KnowledgeReading` of `KnowledgePassage`s. Check the SDK's own README for the exact
signature.

## The `dn` CLI

```sh
dn collections create "Claims policy" --type text --scope-key mission
dn documents add col_... policy.md --title "Claims policy 2026" --pinned --wait
dn documents add col_... m-42-brief.pdf --metadata '{"mission": "M-42"}'
cat rules.md | dn documents add col_... - --title "House rules"
dn documents wait col_...
dn search col_... "receipts over 500 SEK" --scope M-42
dn truth "Should the claim be approved under our policy?" -f claim.json \
  --knowledge col_...:required --knowledge-scope M-42
```

Also `dn documents replace`, `get [--text]`, `list`, `chunks` and `delete`. On a
terminal a knowledge reading prints its passages (number, pinned, title and heading,
score); JSON stays as received. Exit codes: a 409 `knowledge_collection_empty` is 5,
the knowledge 529 is 6.

## Limits and prices

| What | Limit |
|---|---|
| A document's text | 512 KiB once normalised (413 `item_too_large`) |
| A file | 50 MB; a PDF 100 pages |
| `title` | 1 to 200 characters |
| Pinned load | 512 tokens a scope value by default |
| Chunks | 200,000 a workspace |
| Collections, items | 100 and 1,000,000 a workspace, face and text together |
| Writes | An ingestion rate per workspace: a 429 with `details.reason` `ingest_queue_full` or `ingest_tokens_per_hour` and `Retry-After`, retried |

A knowledge reading (`ok`) or a search is one knowledge call, a pinned-only reading
included; a reading that did not run is free. The passages' tokens are input tokens at
the model's price. Reading documents in is billed per newly embedded token (a no-op, a
`PATCH` and a `PUT` back to a text already held are free) and storage per chunk a
month, with a free allowance on the free tier. Current prices:
`https://decisionnode.com/docs/pricing`.

Documents are never used to train or evaluate a model. Every read and every delete
works whatever the workspace's settings, so a knowledge base can always be exported
(`?include=text`) and deleted.
