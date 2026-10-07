#!/usr/bin/env python3
"""Validate SKILL.md front matter and relative links across every skill."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def parse_frontmatter(text):
    """Minimal YAML front matter reader: enough for name/description/allowed-tools."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    data, key, buf = {}, None, []
    for line in m.group(1).split("\n"):
        if re.match(r"^[A-Za-z0-9_-]+:", line):
            if key:
                data[key] = " ".join(buf).strip()
            key, _, rest = line.partition(":")
            key = key.strip()
            buf = [rest.strip().lstrip(">|").strip()]
        elif line.startswith(("  ", "\t")):
            buf.append(line.strip())
    if key:
        data[key] = " ".join(buf).strip()
    return data


skill_files = []
markdown_files = []
for dirpath, _dirnames, filenames in os.walk(os.path.join(ROOT, "plugins")):
    if "SKILL.md" in filenames:
        skill_files.append(os.path.join(dirpath, "SKILL.md"))
    markdown_files += [os.path.join(dirpath, f) for f in filenames if f.endswith(".md") and f != "SKILL.md"]

if not skill_files:
    print("no SKILL.md files found", file=sys.stderr)
    sys.exit(1)

names = {}
for path in sorted(skill_files):
    rel = os.path.relpath(path, ROOT)
    text = open(path, encoding="utf-8").read()
    fm = parse_frontmatter(text)
    if fm is None:
        errors.append(f"{rel}: no YAML front matter")
        continue

    directory = os.path.basename(os.path.dirname(path))
    name = fm.get("name", "")
    desc = fm.get("description", "").strip().strip('"').strip("'")

    if not name:
        errors.append(f"{rel}: front matter has no name")
    elif name != directory:
        errors.append(f"{rel}: name {name!r} does not match directory {directory!r}")
    elif not NAME_RE.match(name):
        errors.append(f"{rel}: name {name!r} is not lowercase kebab-case")
    else:
        if name in names:
            errors.append(f"{rel}: duplicate skill name {name!r} (also {names[name]})")
        names[name] = rel

    if not desc:
        errors.append(f"{rel}: front matter has no description")
    elif len(desc) > 1024:
        errors.append(f"{rel}: description is {len(desc)} chars, limit is 1024")

    # Relative links must resolve, so a reference/ file is never a dead end.
    for link in re.findall(r"\]\((?!https?:|#|mailto:)([^)]+)\)", text):
        target = link.split("#")[0]
        if not target:
            continue
        resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
        if not os.path.exists(resolved):
            errors.append(f"{rel}: broken relative link -> {target}")

# Reference files are read on demand, so their links must resolve too.
for path in sorted(markdown_files):
    text = open(path, encoding="utf-8").read()
    for link in re.findall(r"\]\((?!https?:|#|mailto:)([^)]+)\)", text):
        target = link.split("#")[0]
        if target and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(path), target))):
            errors.append(f"{os.path.relpath(path, ROOT)}: broken relative link -> {target}")

if errors:
    print("Skill validation failed:\n", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)

print(f"OK: {len(skill_files)} skills, front matter valid, links resolve")
