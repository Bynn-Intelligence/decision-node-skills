#!/usr/bin/env python3
"""Bump the patch of the release version in every file that carries it, and print it.

    bump_version.py

The version lives in the files hooks/check_versions.py reads: marketplace.json, one
plugin.json per plugin, metadata.version in every SKILL.md, and server.json. Each
holds it once; a file that does not, or one on another version than server.json,
stops the bump before anything is written.
"""

import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_VERSION = r'^(  "version": ")%s(",?)$'
SKILL_VERSION = r'^(\s+version:\s*"?)%s("?\s*)$'


def main() -> int:
    os.chdir(ROOT)
    current = json.load(open("server.json"))["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", current):
        print("::error::server.json's version %r is not semver" % current)
        return 1
    major, minor, patch = current.split(".")
    new = "%s.%s.%d" % (major, minor, int(patch) + 1)

    files = [(".claude-plugin/marketplace.json", JSON_VERSION), ("server.json", JSON_VERSION)]
    files += [(p, JSON_VERSION) for p in sorted(glob.glob("plugins/*/.claude-plugin/plugin.json"))]
    files += [(p, SKILL_VERSION) for p in sorted(glob.glob("plugins/*/skills/*/SKILL.md"))]
    bumped = {}
    for path, shape in files:
        text = open(path).read()
        pattern = re.compile(shape % re.escape(current), re.M)
        if len(pattern.findall(text)) != 1:
            print("::error::%s does not hold version %s exactly once" % (path, current))
            return 1
        bumped[path] = pattern.sub(lambda m: m.group(1) + new + m.group(2), text)
    for path, text in bumped.items():
        with open(path, "w") as f:
            f.write(text)
    print(new)
    return 0


if __name__ == "__main__":
    sys.exit(main())
