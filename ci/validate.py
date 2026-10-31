#!/usr/bin/env python3
"""Static checks: frontmatter, budgets, references, overlap, ADR indexes, eval coverage. Exit 1 on any failure."""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
from itertools import combinations

import yaml

ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(ROOT)
errors = []
STOP = set("use when or and the a an of to for in on with not from any is are be by as it this that".split())


def err(m):
    errors.append(m)


def fm(path):
    m = re.match(r"^---\n(.*?)\n---\n", open(path).read(), re.S)
    return yaml.safe_load(m.group(1)) if m else None


def nlines(p):
    return sum(1 for _ in open(p))


# ---- skills
skills = {}
for p in sorted(glob.glob("skills/*/SKILL.md")):
    d = os.path.basename(os.path.dirname(p))
    f = fm(p)
    if f is None:
        err(f"{p}: no frontmatter"); continue
    skills[d] = f
    l1 = d.startswith("_")
    for k in ("name", "description", "version"):
        if not f.get(k):
            err(f"{p}: missing `{k}`")
    if not l1 and "adr_tags" not in f:
        err(f"{p}: L2 skill missing `adr_tags`")
    if f.get("name") != d:
        err(f"{p}: name `{f.get('name')}` != dir `{d}`")
    desc = f.get("description", "")
    if not desc.startswith("Use when"):
        err(f"{p}: description must start 'Use when'")
    if len(desc) >= 300:
        err(f"{p}: description {len(desc)} chars (>= 300)")
    if desc.count("Not for") != 1:
        err(f"{p}: description needs exactly one 'Not for' clause")
    if f.get("version") and not re.match(r"^\d+\.\d+\.\d+$", str(f["version"])):
        err(f"{p}: version not SemVer")
    budget = 80 if l1 else 150
    if nlines(p) > budget:
        err(f"{p}: {nlines(p)} lines > {budget}")
    for r in f.get("requires") or []:
        if not os.path.isfile(f"skills/{r}/SKILL.md"):
            err(f"{p}: requires unknown skill {r}")
    body = open(p).read()
    if not l1:
        for sec in ("## Step 0", "## Workflow", "## Output template", "## Calibration"):
            if sec not in body:
                err(f"{p}: missing section `{sec}`")
    # references: named ones exist, no orphans
    named = set(re.findall(r"references/([\w.-]+\.md)", body))
    have = {os.path.basename(x) for x in glob.glob(f"skills/{d}/references/*.md")}
    for n in named - have:
        err(f"{p}: references/{n} named but missing")
    for n in have - named:
        err(f"skills/{d}/references/{n}: orphan (not named in SKILL.md)")
    for s in re.findall(r"scripts/([\w.-]+\.sh)", body):
        if not glob.glob(f"skills/*/scripts/{s}"):
            err(f"{p}: script {s} not found")

for p in glob.glob("skills/*/references/*.md"):
    if nlines(p) > 300:
        err(f"{p}: {nlines(p)} lines > 300")
    if not open(p).readline().startswith("# "):
        err(f"{p}: must start with an H1 title")

# ---- L0 budgets
if nlines("CLAUDE.md") > 50:
    err(f"CLAUDE.md: {nlines('CLAUDE.md')} lines > 50")
for p in glob.glob("demos/*/CLAUDE.md"):
    if nlines(p) > 40:
        err(f"{p}: {nlines(p)} lines > 40")

# ---- duplicated rule text across L0/L1/L2 (normalized bullet-line hash)
seen = {}
for p in ["CLAUDE.md"] + sorted(glob.glob("skills/*/SKILL.md")):
    for line in open(p):
        s = line.strip()
        if not re.match(r"^(-|\d+\.)\s", s):
            continue
        norm = re.sub(r"[^a-z0-9 ]", "", re.sub(r"^(-|\d+\.)\s+", "", s).lower())
        norm = re.sub(r"\s+", " ", norm).strip()
        if len(norm) < 40:
            continue
        h = hashlib.sha1(norm.encode()).hexdigest()
        if h in seen and seen[h] != p:
            err(f"duplicated rule in {p} and {seen[h]}: {s[:70]}")
        seen.setdefault(h, p)

# ---- description overlap between L2 skills
def toks(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 2}

l2 = {k: v for k, v in skills.items() if not k.startswith("_")}
for a, b in combinations(sorted(l2), 2):
    ta, tb = toks(l2[a]["description"]), toks(l2[b]["description"])
    j = len(ta & tb) / max(1, len(ta | tb))
    if j >= 0.5:
        err(f"description overlap {a} / {b}: jaccard {j:.2f} >= 0.5")

# ---- agents
for p in sorted(glob.glob("agents/*.md")):
    f = fm(p) or {}
    if nlines(p) > 60:
        err(f"{p}: {nlines(p)} lines > 60")
    for k in ("name", "description", "tools"):
        if not f.get(k):
            err(f"{p}: missing `{k}`")
    tools = {t.strip() for t in str(f.get("tools", "")).split(",")}
    if tools & {"Edit", "Write", "MultiEdit", "NotebookEdit"}:
        err(f"{p}: subagents are read-only; remove write tools {tools & {'Edit', 'Write', 'MultiEdit', 'NotebookEdit'}}")
    sk = f.get("skills") or []
    for s in [sk] if isinstance(sk, str) else sk:
        if not os.path.isfile(f"skills/{s}/SKILL.md"):
            err(f"{p}: skills: unknown {s}")
    if f.get("name") != os.path.basename(p)[:-3]:
        err(f"{p}: name != filename")

# ---- ADR indexes
for d in ["adrs"] + sorted(glob.glob("demos/*/docs/adr")):
    r = subprocess.run(["skills/_adr/scripts/adr-index.sh", d, "--check"], capture_output=True, text=True)
    if r.returncode:
        err(f"adr-index --check {d} exit {r.returncode}: {r.stderr.strip()}")

# ---- repo settings may add denies, never weaken global denies
glob_settings = json.load(open("settings.json"))
gdeny = glob_settings["permissions"]["deny"]
for p in glob.glob("demos/*/.claude/settings.json"):
    s = json.load(open(p))
    perms = s.get("permissions", {})
    for kind in ("allow", "ask"):
        for rule in perms.get(kind, []):
            inner = re.sub(r"^Bash\((.*)\)$", r"\1", rule).rstrip(":*").rstrip("*").strip()
            for d in gdeny:
                dcmd = re.sub(r"^Bash\((.*)\)$", r"\1", d).split(":")[0].replace(" *", "").strip()
                if rule in ("Bash", "Bash(*)") or dcmd.startswith(inner) or inner.startswith(dcmd):
                    err(f"{p}: permissions.{kind} `{rule}` weakens global deny `{d}`")
    if "disableAllHooks" in s:
        err(f"{p}: repo settings may not disable hooks")

# ---- eval coverage: per L2 skill >= 3 routing, >= 2 shape, >= 1 adr-conflict
cov = {k: {"routing": 0, "shape": 0, "adr-conflict": 0} for k in l2}
for p in glob.glob("tests/evals/**/*.yaml", recursive=True):
    c = yaml.safe_load(open(p))
    if c.get("skill") in cov:
        for k in c.get("kinds", []):
            if k in cov[c["skill"]]:
                cov[c["skill"]][k] += 1
for s, c in cov.items():
    for k, need in (("routing", 3), ("shape", 2), ("adr-conflict", 1)):
        if c[k] < need:
            err(f"evals: {s} has {c[k]} {k} cases (< {need})")

# ---- scripts: strict mode
for p in glob.glob("skills/*/scripts/*.sh") + glob.glob("hooks/*.sh"):
    head = open(p).read(400)
    if "set -euo pipefail" not in head and "set -uo pipefail" not in head:
        err(f"{p}: missing set -euo pipefail")
    if not os.access(p, os.X_OK):
        err(f"{p}: not executable")

if errors:
    print("validate: FAIL\n  " + "\n  ".join(errors))
    sys.exit(1)
print(f"validate: ok ({len(skills)} skills, {len(glob.glob('agents/*.md'))} agents, eval coverage met)")
