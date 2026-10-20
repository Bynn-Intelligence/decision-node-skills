# The `dn` CLI

One native binary for terminals, shell scripts and pipelines. Results on stdout,
everything else on stderr, compact JSON when piped, and exit codes that say what
happened. It is also installed as `bynn-dn`, for systems where `dn` is taken (for
example an oh-my-zsh alias for `dotnet new`).

## Install

```sh
# macOS and Linux: the install script, to ~/.local/bin
curl -fsSL https://raw.githubusercontent.com/Bynn-Intelligence/decision-node-cli/main/install.sh | sh
# Homebrew (macOS and Linux)
brew install bynn-intelligence/bynn/dn
# Scoop (Windows)
scoop bucket add bynn https://github.com/Bynn-Intelligence/scoop-bynn && scoop install dn
```

Direct download: every [release](https://github.com/Bynn-Intelligence/decision-node-cli/releases/latest) has an archive for macOS (arm64, x86-64), Linux (arm64, x86-64, static) and Windows (x86-64, arm64), `.deb` and `.rpm` packages, `checksums.txt`, and a signature of the checksums. For the install script, set `DN_INSTALL_DIR` to install elsewhere, or `DN_VERSION` (for example `v0.1.0`) to pin a version.

## Sign in

```sh
export DECISIONNODE_API_KEY=...        # the environment wins
dn auth login                          # or store it in the system keychain
printf %s "$KEY" | dn auth login --key-stdin
dn auth status                         # where the key comes from; checks it for free
```

There is no `--api-key` flag, so the key never lands in shell history.

## Commands

```
dn truth   <instructions> [state] [--true TEXT] [--false TEXT] [--min P]
dn choice  <instructions> [state] -o NAME[=DESCRIPTION] ...
dn score   <instructions> [state] -l LEVEL ...       (lowest first)
dn number  <instructions> [state] [--min N] [--max N] [--step S]
dn decide  <request.json | ->                         (full request: several questions)
dn upload  <image> ...
dn batch   run <requests.jsonl | -> [--questions FILE] [--out FILE] [--poll S] [--no-wait]
dn batch   run --live <requests.jsonl | -> [--questions FILE] [--concurrency N] [--out FILE] [--resume]
dn batch   create | add | finalize | get | list | results | cancel
dn session <open.json> [--out FILE]                   (frames as JSON Lines on stdin)
dn collections create <name> --type text [--scope-key KEY]
dn documents add <collection_id> <file | -> [--title T] [--reference REF] [--pinned] [--pin-rank N] [--label L] [--metadata JSON] [--wait]
dn documents replace | get [--text] | list | chunks | delete | wait [item_id]
dn search  <collection_id> <query> [--scope VALUE] [--top-k N] [--match JSON] [--filter JSON]
dn models
dn auth    login | status | logout
dn config  get | set | list
dn version
```

State: `-s TEXT`, `-f FILE` (`-` for stdin), or piped stdin.

Images: `--image PATH`, `--image URL` or `--image ID=PATH`, up to 16. A URL is sent
as a URL; a file goes inline when small and is uploaded when large, and the CLI
remembers uploads between runs, so a script that asks about the same large image
many times uploads it once.

Videos: `--video PATH` or `--video ID=PATH`, up to 4, with `--fps` (default 2, at
most 4), `--start`, `--end` and `--max-frames` (default 32, at most 128). The CLI
turns the file into frames on your machine with `ffmpeg` and `ffprobe` from your
`PATH`; only the frames are sent, never the file or its sound.

Boosters: `--booster NAME`, repeatable, in order; `--booster NAME:required` sets
`require`, so a failed or late reading fails the command (exit 6) instead of being
left out. `boosters` in a request file of `dn decide` or a batch line works too,
and is where a booster's options go (`bynn_segment` needs its `prompt`).
The answer is printed first, then the `evidence`.

Knowledge: `--knowledge COLLECTION` on any decision command adds the `knowledge`
booster (`COLLECTION:required` sets `require`), with `--knowledge-scope`,
`--knowledge-top-k` and `--knowledge-query`. `dn documents add` takes a file by path
(converted to text by the API; a small text or Markdown file goes inline) or Markdown
on stdin (`-`); `dn documents wait` waits until the documents are read. On a terminal
a knowledge reading prints its passages (number, pinned, title and heading, score);
JSON stays as received. A 409 `knowledge_collection_empty` exits 5, the knowledge 529
exits 6. More: [knowledge.md](knowledge.md).

Models: `-m decisionnode-flash@acme/fraud` (a fine-tuned model of the key's
workspace) is sent as given. `dn models` shows `fine_tuned`, `base`,
`adapter_version` and `status` for the workspace's fine-tuned models.

Global flags: `-m, --model`, `--flash`, `--base-url`, `--profile`, `--timeout`,
`--retries`, `--json`, `--value`, `--full`, `--meta`, `-q, --quiet`.

## Examples

```sh
dn truth "Is this message a refund request?" -s "I want my money back for order 4411."

# Fail a CI step when a staged diff adds a secret
git diff --staged | dn truth "Does this diff add a secret, key or password?" --min 0.5 && exit 1

dn choice "Which team should handle this?" -f ticket.txt \
  -o billing="Payments and invoices" -o technical="Bugs and outages" -o sales

dn score "How readable is the receipt?" --image receipt.jpg \
  -l unreadable -l "partly readable" -l "fully readable"

dn number "How many line items are on the receipt?" --image receipt.jpg --max 100

dn truth "Is the person in the picture an adult?" --image person.jpg --booster age

dn truth "Does a person fall in the video?" --video dock.mp4 --fps 2

dn collections create "Claims policy" --type text --scope-key mission
dn documents add col_... policy.md --pinned --wait
dn truth "Should the claim be approved under our policy?" -f claim.json \
  --knowledge col_...:required --knowledge-scope M-42

route=$(dn choice "Which queue?" -f ticket.txt -o billing -o bug -o other --value)

cat request.json | dn decide - | jq '.answers.route.choice'

dn batch run tickets.jsonl --questions triage.json --out results.jsonl
```

## Output

| Mode | When | Prints |
|---|---|---|
| Human | stdout is a terminal | The answer in aligned lines, probabilities highest first |
| JSON | piped, or `--json` | The answer object as the API sent it, for example `{"type":"truth","truth":0.94}` |
| Value | `--value` | Only the probability, the option name, the number or the score |

`--min P` (truth only) exits 1 when the probability is below `P`. `--full` prints
the whole response body for a single-question command. `--meta` adds `request_id`,
`model`, `latency_ms`, `input_tokens` and `safety`.

`dn batch run` uses the Batch API, for less than live calls: DecisionNode Flash at
50% off the live price and DecisionNode MoE at 30% off. A batch has no set
finishing time, so `dn` polls it every `--poll` seconds (default 60); requests
still unanswered 24 hours after it is finalized expire, unbilled. `--live` sends
the lines as live requests instead, `--concurrency` at a time, and `--resume`
skips lines already in `--out`. Both read JSON Lines (full requests, or states
with `--questions`) and write `{"index", "id", "response"}` or `{"index", "id",
"error"}` per line in input order. Exit codes: [errors.md](errors.md).

Settings live in `~/.config/decisionnode/config.toml`, with named profiles chosen
by `--profile` or `DECISIONNODE_PROFILE`.
