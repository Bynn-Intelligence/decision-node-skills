# Requests, questions and answers

## The request

```json
{
  "model": "decisionnode-moe",
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
| `model` | Optional. Defaults to `decisionnode-moe`. A family id (`decisionnode-moe`, `decisionnode-flash`: the current release), a pinned id from `GET /v1/models` (`decisionnode-<family>-<version>`), or a fine-tuned model of the key's workspace (below). The older ids `decisionnode-1.0`, `decisionnode-1.0-flash`, `decisionnode-latest` and `decisionnode-flash-latest` are still accepted. |
| `state` | A string, object or array. Objects are read with their keys. Left out or `""` when there is nothing to evaluate. |
| `questions` | A map of id to question, at least one. Any mix of types. The token limit of the model is the only bound on the count. |
| `images` | Optional, up to 16. See below. |
| `videos` | Optional, up to 4, sent as frames. See below. |
| `boosters` | Optional, up to 4. See below. |
| `fallback` | Optional, default `true`: a request for `decisionnode-moe` that no ready worker can take at once is answered by `decisionnode-flash`, with `x-decisionnode-fallback` and `x-decisionnode-requested-model` naming the two. `false`: the 529 with `Retry-After` instead. Live `decide` only; a pinned id never falls back. |

A field sent as `null` equals a field left out.

## Question fields

| Type | `instructions` | Other fields |
|---|---|---|
| `truth` | What to judge. Needs `instructions` or `criteria`. | `criteria`, optional: `{"true": ..., "false": ...}`, either side alone is fine |
| `choice` | What to decide | `criteria`, required: `{name: description}`, 1 to 255 options. A description may be `null`. |
| `score` | What to measure | `criteria`, required: a list of 1 to 10 levels, lowest first |
| `number` | What to count or read. Required. | `min`, `max`, `step`, optional: the grid of possible answers (default 0 to 255 by 1). `min: 0, max: 5, step: 0.5` is a rating in halves. |
| `point`, `box` | What to find. Required. | `image`: the id of the image to look in, required with two or more images. `units`: `pixels` (default) or `normalized`. |

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
- **Say which image.** With two or more images, name the image in each question,
  by id in backticks (give images short names such as `receipt`, not digits) or by
  number from 1 in array order ("image 2"). The `image` field of a point or box
  takes the id.
- **No state, no evidence.** A question asked without the facts it needs gets a
  flat answer with low confidence, not an error.

## Answers

```json
{
  "model": "decisionnode-moe-<version>",
  "answers": {
    "route": { "type": "choice", "choice": "billing", "confidence": 0.81,
               "probabilities": { "account": 0.05, "billing": 0.87, "bug": 0.08 } },
    "urgency": { "type": "score", "score": 2.31, "confidence": 0.31,
                 "legend": { "0": "routine", "1": "today", "2": "urgent", "3": "critical" },
                 "probabilities": { "0": 0.01, "1": 0.09, "2": 0.48, "3": 0.42 } },
    "escalate": { "type": "truth", "truth": 0.94 }
  },
  "usage": { "input_tokens": 62, "output_tokens": 0,
             "cost": { "usd": 0.000002604, "model_usd": 0.000002604, "boosters_usd": 0, "free_tier": false } }
}
```

| Field | Meaning |
|---|---|
| `truth` | Probability of yes, 0 to 1. No confidence field: the distance from 0.5 is the confidence. |
| `choice` | The most probable option |
| `score` | Expected level index, the sum of index times probability |
| `number` | The most probable value of the grid; `expected` is the probability-weighted mean |
| `confidence` | Choice and score: 0 means no better than a uniform guess, 1 means certain. Number: the probability of `number`. |
| `probabilities` | Every option or level, zeros included, keyed by option name or by level index as a string. A number's lists the values above 0.001, keyed by the value as a string (`"7"`, `"3.5"`). |
| `legend` | Level index to the level exactly as sent |
| `model` | The pinned id of the version that answered, `decisionnode-<family>-<version>` |
| `usage.cost` | What the answer cost in USD: `usd` (the amount booked), split into `model_usd` and `boosters_usd`, and `free_tier` (`true` when the free tier covered the model's part, which is then 0). Amounts have up to 9 decimals. A refused or unbilled answer carries zeros. Read `usd` as sent; do not add the parts yourself. The amounts in these examples are examples, not prices. |

Point and box answers:

```json
"pick":   { "type": "point", "x": 812, "y": 455, "present": 0.97, "confidence": 0.91, "image": "belt", "width": 1920, "height": 1080 },
"damage": { "type": "box", "x1": 300, "y1": 120, "x2": 520, "y2": 410, "present": 0.95, "confidence": 0.88, "image": "belt", "width": 1920, "height": 1080 }
```

`x` to the right and `y` down from the top-left corner, in pixels of the image as
sent (fractions with `units: "normalized"`). `present` is the probability that the
thing is in the image at all; `confidence` that the place is right if it is. Under a
low `present` the place is only a best guess.

A request succeeds for all questions or fails as a whole. There are no partial
answers. Response headers carry `x-request-id`, `x-decisionnode-model` and
`x-decisionnode-latency-ms`.

## Patterns

| Goal | Pattern |
|---|---|
| Route a ticket | `choice` over the queues, with an `other` option |
| Moderate or gate | `truth` per rule, thresholds in your code |
| Prioritise | `score` on an urgency or severity scale |
| Count or read a quantity | `number` with a grid that covers every plausible value |
| Find something in an image | `point`, or `box` to crop or draw it; check `present` first |
| Check a claim against a source | State `{"source": ..., "claim": ...}`, `truth` "Is the claim supported by the source?" |
| Extract a field from a fixed set | `choice` over the candidates, for example currencies |
| Verify a document image | Expected values in the state, one `truth` per field: "Does the total on the receipt equal the total in the claim?" |
| Check the person or the picture | `truth` questions with the `age` or `ai_generated` booster |
| Match a face against your own people | `truth` questions with the `face_recognition` booster on one of your face collections |
| Read the text in a picture | `truth` or `choice` questions with the `ocr` booster |
| Steer a robot or a drone | `truth` ("Is the path ahead clear for 2 meters?") and `point` questions with the `bynn_depth` and `bynn_segment` boosters |
| Many records | `decide_many`, the Batch API, or `dn batch run` |

## Images

```json
{
  "state": { "claim": { "total": "740.00", "currency": "SEK" } },
  "images": [ { "id": "receipt", "url": "https://files.example.com/claims/4411/receipt.jpg" } ],
  "questions": {
    "total_matches": { "type": "truth", "instructions": "Does the total on the receipt equal the total in the claim?" },
    "legible": { "type": "score", "instructions": "How readable is the receipt?",
                 "criteria": ["unreadable", "partly readable", "fully readable"] }
  }
}
```

An image is `{id, url}` with an `https` URL (the fastest form: nothing is
uploaded), `{id, data, media_type}` with base64 bytes (`image/jpeg`, `image/png` or
`image/webp`), or `{id, upload_id}` naming an upload of the same workspace from
`POST /v1/uploads`, valid for one hour. Up to 16 per request, 10 MB each, within the
model's token limit: image tokens count toward it and are part of
`usage.input_tokens`. A request body is at most 25 MiB (26,214,400 bytes); inline
base64 counts toward it, so images of more than about a megabyte go as uploads or
URLs. The SDKs and the CLI pick the form for local files.

## Videos

```json
{
  "state": "Warehouse camera 4, loading dock.",
  "videos": [
    { "id": "dock", "fps": 2, "frames": [
        { "t": 30.0, "media_type": "image/jpeg", "data": "<base64>" },
        { "t": 30.5, "media_type": "image/jpeg", "data": "<base64>" } ] }
  ],
  "questions": {
    "fall": { "type": "truth", "instructions": "Does a person fall in the video?" },
    "forklifts": { "type": "number", "instructions": "How many forklifts pass the door?", "min": 0, "max": 50 }
  }
}
```

A video is the frames you sampled, each with its time `t` in seconds, increasing.
`fps` caps the rate read (above 0, at most 4, default 2); `start` and `end` pick a
window on the frames' times. Up to 4 videos and 128 frames per request. Video files
and URLs are not taken, and sound is not read. A response to a request with videos
adds `usage.video_frames`, `usage.video_seconds` and, when the server read fewer
frames or a lower resolution than sent, `warnings`.

## Boosters

```json
{
  "model": "decisionnode-moe-<version>",
  "images": [
    { "id": "person", "upload_id": "upl_..." },
    { "id": "poster", "url": "https://files.example.com/poster.jpg" }
  ],
  "boosters": ["age", "ai_generated"],
  "questions": {
    "adult": { "type": "truth", "instructions": "Is the person in the first picture an adult?" },
    "synthetic": { "type": "truth", "instructions": "Is the second picture AI-generated?" }
  }
}
```

A plain list of names is the normal form. A booster that needs an option is an
object with its `name`; here `ai_generated` reads only the second picture, and the
request fails if it cannot:

```json
"boosters": ["age", { "name": "ai_generated", "images": ["poster"], "require": true }]
```

| Field | Notes |
|---|---|
| `boosters` | Up to 4 entries, each a booster name or an object, each booster at most once. `null` and `[]` mean none. |
| `name` (in an object) | The booster's name. An object takes only `name`, `images`, `require` and `options`. |
| `images` (in an object) | The request's image ids the booster reads. Left out: every image. |
| `require` (in an object) | `true`: a booster that fails or does not answer in time fails the request with the 529 `booster_unavailable`. Otherwise the decision runs without that reading. |
| `options` (in an object) | Settings of a booster: `face_recognition` takes `collection` (required: `celebrities`, the public collection, or the id of one of your workspace's face collections) and `threshold` (0 to 1, default 0.5); `ocr` takes `prompt`; `bynn_depth` takes `grid_size` (2 to 16, default 8); `bynn_segment` takes `prompt` (required: one phrase as a string, or an array of 1 to 4, each at most 120 characters), `max_instances` (1 to 16, default 8), `min_score` (0 to 1, default 0.25), `polygon_points` (3 to 64, default 24) and `depth` (default `true`). `age`, `ai_generated` and `face_detection` take none. Any other key or value is a 400 `api_usage_error`. |

Boosters belong to the request, not to a question: every question sees every
reading. Each has a time budget (800 ms; `ocr` more, so give a request naming it 30 s
per attempt and never retry it after a timeout) and they run side by side. Batch lines
take `boosters` like a live request; sessions do not (a 400).

The response:

```json
{
  "model": "decisionnode-moe-<version>",
  "answers": {
    "adult": { "type": "truth", "truth": 0.97 },
    "synthetic": { "type": "truth", "truth": 0.91 }
  },
  "evidence": {
    "age": {
      "version": "age-v3", "status": "ok", "latency_ms": 212, "billed_calls": 2,
      "results": [
        { "image": "person", "age_years": 27, "low": 22, "high": 33, "confidence": 0.81, "faces": 1 },
        { "image": "poster", "faces": 0 }
      ]
    },
    "ai_generated": {
      "version": "ai_generated-v2", "status": "ok", "latency_ms": 340, "billed_calls": 1,
      "results": [
        { "image": "poster", "generated": 0.93, "confidence": 0.86, "method": "inference",
          "top_generator": { "name": "<generator>", "probability": 0.71 }, "c2pa_signer": null }
      ]
    }
  },
  "usage": { "input_tokens": 341, "output_tokens": 0, "booster_tokens": 72, "boosters": 3,
             "cost": { "usd": 0.036014322, "model_usd": 0.000014322, "boosters_usd": 0.036, "free_tier": false } }
}
```

| Field | Notes |
|---|---|
| `evidence` | One entry per booster the request named, in its order. Only when the request named boosters. |
| `evidence.<name>.billed_calls` | The calls of this booster billed on this request: one per image it read with status `ok`, a reading reused from a cache included, and 0 for a booster that failed or timed out and for a refused request. The entries sum to `usage.boosters`. |
| `evidence.<name>.status` | `ok`; `timeout` (no answer within its budget); `error`; `skipped` (none of the request's images is one it reads). With `timeout` or `error`, `results` lists `{"image": id}` with no reading for each picture the booster was meant to read; with `skipped` it is empty. Within an `ok` entry, a picture the booster could not decode reads `{"image": id, "readable": false}` and is not billed. |
| `evidence.<name>.results` | One entry per image read, named by `image`. `age`: `age_years`, `low`, `high`, `confidence`, `faces` (with `faces` 0 the age fields are left out). `ai_generated`: `generated` (probability the picture was made by a generator), `confidence`, `method` (`inference` from the pixels, `c2pa` when the file's trusted Content Credentials declare it generated or edited by AI, which overrides the pixels), `top_generator` (`name`, `probability`; `null` unless an `inference` reading says likely generated, and always `null` on a `c2pa` reading), `c2pa_signer` (who signed trusted Content Credentials, else `null`), and `c2pa: "untrusted"` only when the file's Content Credentials validate but are not trusted (no signer, no override). A photograph reads `"top_generator": null`. |
| `evidence.<name>.results` for `face_detection` | `faces` (how many; 0 is a reading) and `detections` (most confident first, `[]` when there is none): each a `box` with the corners `x1`, `y1`, `x2`, `y2` (pixels of the image as sent, or fractions when the request's point and box questions ask for `normalized` units) and a `confidence`, 0 to 1 |
| `evidence.<name>.results` for `face_recognition` | `faces` (the faces searched) and `matches` (best first, `[]` when none passes the threshold): each a `box`, a `score` (0 to 1), the `collection` searched and the matched item's `reference`, with `label` for your own item or `name` for a public figure. A match is evidence, never an answer |
| `evidence.<name>.results` for `ocr` | `text` (the reading, in the format the prompt asks for; empty when the picture shows no text) and `truncated` |
| `evidence.<name>.results` for `bynn_depth` | `ahead` (meters to the nearest obstacle straight ahead, in the middle third of the picture, the floor left out; `null` when none is found), `directions` (7 entries for 7 vertical strips, left to right, each meters or `null`), `ground` (`true` when a floor was found and left out), `grid_rows`, `grid_cols` and `grid` (meters, row by row from the top left), `depth_min`, `depth_max`, `depth_median`, `width`, `height` (pixels) |
| `evidence.<name>.results` for `bynn_segment` | `width`, `height`, `prompts` (the phrases searched for), `instances` (best first, `[]` when nothing is found): `label` (the phrase it matched), `score`, `box` `[x1, y1, x2, y2]`, `polygon`, `area`, `centroid` `[x, y]`, `opening` (the hole of a gate, doorway or ring, else `null`), `depth` (`median`, `opening_median`, `opening_rim_median` in meters) and `size_m`; then `depth_source` and `assumed_hfov_deg`. Coordinates are fractions from the top left. |
| `usage.booster_tokens` | The readings' share of `input_tokens`, counted once per request |
| `usage.boosters` | The booster calls billed: one per booster and image read with status `ok` |

Every response of a request that named boosters, errors included, carries
`x-decisionnode-boosters` with each booster's status and time in request order:
`age=ok:212,ai_generated=timeout:800`. Each booster call billed has a price, drawn
from the prepaid balance with the request's tokens, and the readings' tokens are
input tokens at the model's price; the current prices are on
`https://decisionnode.com/docs/pricing`. A timed-out or failed booster is free, and a request
refused by the safety check pays nothing for its boosters. Every booster is on for
a new workspace; an owner or admin can turn one off in the console.

### Robots and drones

Depth Vision (`bynn_depth`) and Segment Vision (`bynn_segment`) read a camera picture
for a machine that moves: how far away things are, and where the things you name are.
Ask the question your code acts on and read its answer; the readings are evidence.

```json
{
  "state": {"vehicle": "drone", "altitude_m": 1.5, "task": "fly through the next gate"},
  "images": [{ "id": "front", "upload_id": "upl_..." }],
  "boosters": [
    { "name": "bynn_depth", "options": { "grid_size": 8 } },
    { "name": "bynn_segment", "options": { "prompt": ["purple gate", "orange H landing pad"] } }
  ],
  "questions": {
    "clear": { "type": "truth", "instructions": "Is the path straight ahead clear for at least 2 meters?" },
    "gate": { "type": "point", "instructions": "The centre of the opening of the purple gate.", "units": "normalized" }
  }
}
```

A Segment Vision reading of that picture:

```json
{ "image": "front", "width": 1280, "height": 720, "prompts": ["purple gate", "orange H landing pad"],
  "instances": [
    { "label": "purple gate", "score": 0.91, "box": [0.31, 0.22, 0.58, 0.81],
      "polygon": [[0.31, 0.22], [0.58, 0.22], [0.58, 0.81], [0.31, 0.81]], "area": 0.12,
      "centroid": [0.45, 0.47], "opening": null,
      "depth": { "median": 4.2, "opening_median": null, "opening_rim_median": null },
      "size_m": { "width": 1.6, "height": 2.1, "opening": null } } ],
  "depth_source": "bynn_depth", "assumed_hfov_deg": 65 }
```

- Descriptive phrases match better than one word: "orange H landing pad", "purple
  octagonal frame on a pole".
- With `depth` on (the default), each match carries its distance and size in meters;
  the sizes assume the field of view in `assumed_hfov_deg`.
- The distances and sizes are estimates from one picture, for decisions and planning,
  never a safety stop: a robot or a drone uses stereo cameras or LiDAR for that.
- Each picture a booster reads is one booster call, depth inside Segment Vision
  included.

## Fine-tuned models

A fine-tuned model is trained in the console on decisions a workspace has
labelled, and is called by the keys of that workspace only:

```
<base>@<workspace-slug>/<name>        the version deployed now
<base>@<workspace-slug>/<name>:<n>    version n
```

`<base>` is a family id, `decisionnode-moe` or `decisionnode-flash` (the older
`decisionnode-1.0` and `decisionnode-1.0-flash` are still accepted), for example
`decisionnode-flash@acme/fraud:3`. It answers like its base: the same question
types, answer shapes, limits and errors. The response's `model` and
`x-decisionnode-model` carry the pinned name. A name that does not exist, a version
that is not deployed and another workspace's model are all the 400
`{"detail": {"error_type": "api_usage_error", "message": "Unknown model: <name>"}}`.
`GET /v1/models` lists the workspace's deployed and ready versions under their
pinned names, and the plain name of each model with a deployed version, each with
`fine_tuned: true`, `base`, `family` (`decisionnode-moe` or `decisionnode-flash`), `adapter_version` and `status` (`deployed` or `ready`;
only `deployed` answers decisions). A fine-tuned model is billed at its base's
price per input token plus a premium; the current prices are on
`https://decisionnode.com/docs/pricing`.
