#!/usr/bin/env python3
"""Validate every JSON file, the marketplace and plugin manifests, and server.json.

The check that matters most here is that every plugin `source` starts with "./".
The skills CLI validates it with a literal `path.startsWith("./")`, and a source
that fails it is skipped silently: skills still install through the CLI's
recursive fallback, but plugin grouping disappears and the installer shows one
flat list instead of per-product groups. Nothing errors, so only a test catches it.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []


def err(msg):
    errors.append(msg)


def load(path):
    try:
        with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        err(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        err(f"invalid JSON in {path}: {exc}")
    return None


# Every JSON file in the repository must parse.
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules"}]
    for fn in filenames:
        if fn.endswith(".json"):
            load(os.path.relpath(os.path.join(dirpath, fn), ROOT))

# server.json, the MCP registry entry.
server = load("server.json")
if server is not None:
    for key in ("$schema", "name", "description", "version", "remotes"):
        if key not in server:
            err(f"server.json missing required key: {key}")
    if not str(server.get("name", "")).count("/") == 1:
        err("server.json name must be reverse-DNS namespace and name, like com.example/server")
    if len(server.get("description", "")) > 100:
        err("server.json description is longer than 100 characters")
    for remote in server.get("remotes", []):
        if remote.get("type") not in ("streamable-http", "sse"):
            err(f"server.json remote type {remote.get('type')!r} is not streamable-http or sse")
        if not str(remote.get("url", "")).startswith("https://"):
            err("server.json remote url must be https")

market = load(".claude-plugin/marketplace.json")
if market is None:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)

for key in ("name", "description", "owner", "plugins"):
    if key not in market:
        err(f"marketplace.json missing required key: {key}")

if "metadata" in market and "pluginRoot" in market.get("metadata", {}):
    err(
        "marketplace.json sets metadata.pluginRoot. Combined with a bare plugin "
        "source this breaks grouping in the skills CLI. Use a full "
        '"source": "./plugins/<name>" instead.'
    )

seen_names = set()
for plugin in market.get("plugins", []):
    name = plugin.get("name")
    if not name:
        err("a plugin entry has no name")
        continue
    if name in seen_names:
        err(f"duplicate plugin name: {name}")
    seen_names.add(name)

    source = plugin.get("source")
    if not isinstance(source, str):
        err(f"[{name}] source must be a string")
        continue
    # isValidRelativePath() in the skills CLI is exactly path.startsWith("./")
    if not source.startswith("./"):
        err(
            f'[{name}] source "{source}" must start with "./" or the skills CLI '
            f"skips this plugin and grouping silently stops working"
        )
        continue

    plugin_dir = os.path.join(ROOT, source)
    if not os.path.isdir(plugin_dir):
        err(f"[{name}] source directory does not exist: {source}")
        continue

    manifest_path = os.path.join(source, ".claude-plugin", "plugin.json")
    manifest = load(manifest_path)
    if manifest is None:
        continue

    if manifest.get("name") != name:
        err(
            f"[{name}] plugin.json name is {manifest.get('name')!r}, "
            f"marketplace says {name!r}"
        )

    market_skills = plugin.get("skills") or []
    plugin_skills = manifest.get("skills") or []
    if not market_skills:
        err(f"[{name}] marketplace entry declares no skills")
    if sorted(market_skills) != sorted(plugin_skills):
        only_market = sorted(set(market_skills) - set(plugin_skills))
        only_plugin = sorted(set(plugin_skills) - set(market_skills))
        err(
            f"[{name}] skills lists disagree. "
            f"only in marketplace.json: {only_market}. "
            f"only in plugin.json: {only_plugin}"
        )

    for skill in market_skills:
        if not skill.startswith("./"):
            err(f'[{name}] skill path "{skill}" must start with "./"')
            continue
        skill_md = os.path.join(plugin_dir, skill, "SKILL.md")
        if not os.path.isfile(skill_md):
            err(f"[{name}] declared skill has no SKILL.md: {skill}")

    # Every skill on disk should be declared, or it ships ungrouped.
    skills_dir = os.path.join(plugin_dir, "skills")
    if os.path.isdir(skills_dir):
        declared = {os.path.basename(s.rstrip("/")) for s in market_skills}
        for entry in sorted(os.listdir(skills_dir)):
            if not os.path.isdir(os.path.join(skills_dir, entry)):
                continue
            if entry not in declared:
                err(f"[{name}] skill on disk is not declared in the manifests: {entry}")

if errors:
    print("Manifest validation failed:\n", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)

count = sum(len(p.get("skills") or []) for p in market["plugins"])
print(f"OK: {len(market['plugins'])} plugins, {count} skills, all paths resolve")
