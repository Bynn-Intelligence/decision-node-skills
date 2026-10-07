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
dn decide  <request.json | ->                         (full request: several questions)
dn batch   <requests.jsonl | -> [--questions FILE] [--concurrency N] [--out FILE] [--resume]
dn models
dn auth    login | status | logout
dn config  get | set | list
```

State: `-s TEXT`, `-f FILE` (`-` for stdin), or piped stdin. Images:
`--image PATH`, `--image URL` or `--image ID=PATH`, up to four.

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

route=$(dn choice "Which queue?" -f ticket.txt -o billing -o bug -o other --value)

cat request.json | dn decide - | jq '.answers.route.choice'

dn batch tickets.jsonl --questions triage.json --out results.jsonl --resume
```

## Output

| Mode | When | Prints |
|---|---|---|
| Human | stdout is a terminal | The answer in aligned lines, probabilities highest first |
| JSON | piped, or `--json` | The answer object as the API sent it, for example `{"type":"truth","truth":0.94}` |
| Value | `--value` | Only the probability, the option name or the score |

`--min P` (truth only) exits 1 when the probability is below `P`. `--meta` adds
`request_id`, `model`, `latency_ms`, `input_tokens` and `safety`.

`dn batch` reads JSON Lines (full requests, or states with `--questions`) and
writes `{"index", "id", "response"}` or `{"index", "id", "error"}` per line in input
order. Exit codes: [errors.md](errors.md).

Settings live in `~/.config/decisionnode/config.toml`, with named profiles chosen
by `--profile` or `DECISIONNODE_PROFILE`.
