# The `dn` CLI

One native binary for terminals, shell scripts and pipelines. Results on stdout,
everything else on stderr, compact JSON when piped, and exit codes that say what
happened. It is also installed as `bynn-dn`, for systems where `dn` is taken (for
example an oh-my-zsh alias for `dotnet new`).

## Install

```sh
curl -fsSL https://decisionnode.com/install.sh | sh     # macOS, Linux
brew install bynn-intelligence/bynn/dn                  # Homebrew
npm install -g @bynn/dn                                 # or: npx -y @bynn/dn <command>
scoop bucket add bynn https://github.com/Bynn-Intelligence/scoop-bynn && scoop install dn
```

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
left out. `boosters` in a request file of `dn decide` or a batch line works too.
The answer is printed first, then the `evidence`.

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

`dn batch run` uses the Batch API: a lower price, results within 24 hours, polled
every `--poll` seconds (default 60). `--live` sends the lines as live requests
instead, `--concurrency` at a time, and `--resume` skips lines already in `--out`.
Both read JSON Lines (full requests, or states with `--questions`) and write
`{"index", "id", "response"}` or `{"index", "id", "error"}` per line in input
order. Exit codes: [errors.md](errors.md).

Settings live in `~/.config/decisionnode/config.toml`, with named profiles chosen
by `--profile` or `DECISIONNODE_PROFILE`.
