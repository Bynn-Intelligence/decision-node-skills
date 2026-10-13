#!/usr/bin/env python3
"""Sign in to the MCP registry by DNS, with the request and token file of `mcp-publisher login dns`.

    MCP_REGISTRY_PRIVATE_KEY=<64 hex> registry_login.py --domain DOMAIN [--registry URL]

mcp-publisher takes the private key only as a command-line argument, where every
process on the machine can read it. This reads it from the environment instead,
writes it to a file only this user can read (mode 0600, in a directory of mode 0700),
has openssl sign the current timestamp with it, and removes the file. The registry's
token for the signature is saved to ~/.config/mcp-publisher/token.json (mode 0600),
where `mcp-publisher publish` reads it. The key is never printed.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from typing import List

REGISTRY = "https://registry.modelcontextprotocol.io"
# PKCS#8 for an Ed25519 key, before the 32-byte seed (RFC 8410).
PKCS8_ED25519 = bytes.fromhex("302e020100300506032b657004220420")


def sign(seed: bytes, message: bytes) -> bytes:
    old = os.umask(0o077)
    try:
        with tempfile.TemporaryDirectory() as directory:
            key = os.path.join(directory, "key.der")
            fd = os.open(key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(PKCS8_ED25519 + seed)
            data = os.path.join(directory, "timestamp")
            with open(data, "wb") as f:
                f.write(message)
            signed = subprocess.run(
                ["openssl", "pkeyutl", "-sign", "-rawin", "-keyform", "DER", "-inkey", key, "-in", data],
                capture_output=True,
            )
    finally:
        os.umask(old)
    if signed.returncode != 0 or len(signed.stdout) != 64:
        raise SystemExit("::error::openssl could not sign with MCP_REGISTRY_PRIVATE_KEY")
    return signed.stdout


def main(argv: List[str]) -> int:
    args = dict(zip(argv[::2], argv[1::2]))
    domain = args.get("--domain", "")
    registry = args.get("--registry", REGISTRY).rstrip("/")
    if len(argv) % 2 or not domain or set(args) - {"--domain", "--registry"}:
        print("usage: registry_login.py --domain DOMAIN [--registry URL]", file=sys.stderr)
        return 2
    key = os.environ.get("MCP_REGISTRY_PRIVATE_KEY", "").strip()
    if not re.fullmatch(r"[0-9a-fA-F]{64}", key):
        print("::error::MCP_REGISTRY_PRIVATE_KEY is not a 64-character hex Ed25519 key")
        return 1

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    signature = sign(bytes.fromhex(key), timestamp.encode())
    body = json.dumps({"domain": domain, "timestamp": timestamp, "signed_timestamp": signature.hex()})
    request = urllib.request.Request(
        "%s/v0/auth/dns" % registry,
        data=body.encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            token = json.load(response)["registry_token"]
    except urllib.error.HTTPError as e:
        print("::error::the registry refused the DNS sign-in: %d %s" % (e.code, e.read().decode("utf-8", "replace")))
        return 1
    except (urllib.error.URLError, ValueError, KeyError) as e:
        print("::error::the registry's answer to the DNS sign-in was not a token: %s" % type(e).__name__)
        return 1

    directory = os.path.join(os.path.expanduser("~"), ".config", "mcp-publisher")
    os.makedirs(directory, mode=0o700, exist_ok=True)
    path = os.path.join(directory, "token.json")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump({"token": token, "method": "dns", "registry": registry}, f)
    os.chmod(path, 0o600)
    print("Signed in to %s for %s" % (registry, domain))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
