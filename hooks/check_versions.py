#!/usr/bin/env python3
"""Every version in the repository must agree.

The version lives in marketplace.json, one plugin.json per plugin,
metadata.version in every SKILL.md, and server.json. Plugin clients only deliver
an update when the plugin version is bumped, so a manifest left behind on an old
version means those users silently never receive the change.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
found = {}
errors = []


def record(path, version):
    if version is None:
        errors.append(f"{path}: no version field")
        return
    if not SEMVER.match(str(version)):
        errors.append(f"{path}: version {version!r} is not semver")
        return
    found.setdefault(str(version), []).append(path)


market = json.load(open(".claude-plugin/marketplace.json"))
record(".claude-plugin/marketplace.json", market.get("version"))

record("server.json", json.load(open("server.json")).get("version"))

for p in sorted(glob.glob("plugins/*/.claude-plugin/plugin.json")):
    record(p, json.load(open(p)).get("version"))

for p in sorted(glob.glob("plugins/*/skills/*/SKILL.md")):
    m = re.search(r'^\s+version:\s*"?([^"\n]+)"?\s*$', open(p).read(), re.M)
    record(p, m.group(1).strip() if m else None)

if len(found) > 1:
    errors.append("versions disagree across the repository:")
    for version, paths in sorted(found.items()):
        errors.append(f"  {version}: {len(paths)} file(s)")
        for path in paths[:4]:
            errors.append(f"    - {path}")
        if len(paths) > 4:
            errors.append(f"    ... and {len(paths) - 4} more")

if errors:
    print("Version check failed:\n", file=sys.stderr)
    for e in errors:
        print(f"  {e}" if e.startswith(" ") else f"  - {e}", file=sys.stderr)
    sys.exit(1)

version = next(iter(found))
total = sum(len(v) for v in found.values())
print(f"OK: all {total} version fields agree at {version}")
