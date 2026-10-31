#!/usr/bin/env python3
"""ADR parsing, validation, indexing and resolution.

Python 3.9+ and PyYAML. Read-only except `index` (writes INDEX.md).
Exit codes: 0 ok, 1 stale index, 2 invalid frontmatter / unknown tag / bad link.
"""
import argparse
import datetime as dt
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys

import yaml

ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", ".."))
GLOBAL_DIR = os.environ.get("AGENT_CONFIG_ADRS", os.path.join(ROOT, "adrs"))
TAGS_FILE = os.path.join(GLOBAL_DIR, "TAGS.md")

STATUSES = {"proposed", "accepted", "deprecated", "superseded"}
REQUIRED = ["id", "title", "status", "scope", "tags", "enforce", "date", "owners"]
SECTIONS = ["Context", "Decision", "Rules", "Consequences", "Exceptions"]

# file glob -> inferred tags (section 5.4 step 1)
FILE_TAGS = [
    ("*.tf", ["terraform", "iac"]), ("*.tfvars", ["terraform", "iac"]),
    ("Chart.yaml", ["helm", "k8s"]), ("values*.yaml", ["helm", "k8s"]),
    ("kustomization.yaml", ["k8s"]), ("*/k8s/*.yaml", ["k8s"]), ("*/deploy/*.yaml", ["k8s"]),
    ("*.py", ["code", "python"]), ("*.go", ["code", "go"]), ("*.ts", ["code", "typescript"]),
    (".github/workflows/*", ["ci"]), ("*.avsc", ["schema"]), ("*.proto", ["schema"]),
]


class AdrError(Exception):
    pass


def load_tags():
    tags = set()
    with open(TAGS_FILE) as f:
        for line in f:
            m = re.match(r"^\|\s*([a-z0-9-]+)\s*\|", line)
            if m and m.group(1) != "tag":
                tags.add(m.group(1))
    return tags


def _yq_frontmatter(path):
    """Spec 7: parse frontmatter with yq (mikefarah v4). Returns None to fall back to PyYAML."""
    r = subprocess.run(["yq", "-o=json", "--front-matter=extract", ".", path], capture_output=True, text=True)
    if r.returncode != 0:
        raise AdrError(f"{path}: bad YAML frontmatter: {r.stderr.strip()}")
    fm = json.loads(r.stdout or "{}") or {}
    if isinstance(fm.get("date"), str):
        try:
            fm["date"] = dt.date.fromisoformat(fm["date"])
        except ValueError:
            pass
    return fm


def _norm_id(v):
    """Unquoted `id: 0012` parses as int 12; repo ids are 4-digit strings."""
    return f"{v:04d}" if isinstance(v, int) else str(v)


def parse(path):
    text = open(path).read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise AdrError(f"{path}: missing YAML frontmatter")
    fm = _yq_frontmatter(path) if shutil.which("yq") else None
    if fm is None:
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            raise AdrError(f"{path}: bad YAML: {e}")
    body = m.group(2)
    sections, cur = {}, None
    for line in body.splitlines():
        h = re.match(r"^##\s+(\w+)", line)
        if h:
            cur = h.group(1)
            sections[cur] = []
        elif cur:
            sections[cur].append(line)
    fm["_sections"] = {k: "\n".join(v).strip() for k, v in sections.items()}
    fm["_path"] = path
    fm["id"] = _norm_id(fm.get("id", ""))
    if fm.get("supersedes"):
        fm["supersedes"] = [_norm_id(x) for x in fm["supersedes"]]
    if fm.get("superseded_by") not in (None, ""):
        fm["superseded_by"] = _norm_id(fm["superseded_by"])
    return fm


def validate(adr, tags, scope):
    p, errs = adr["_path"], []
    for k in REQUIRED:
        if adr.get(k) in (None, "", []):
            errs.append(f"{p}: missing `{k}`")
    if adr.get("status") not in STATUSES:
        errs.append(f"{p}: status `{adr.get('status')}` not in {sorted(STATUSES)}")
    if adr.get("scope") != scope:
        errs.append(f"{p}: scope `{adr.get('scope')}` but file is in a {scope} ADR dir")
    if adr.get("enforce") not in ("must", "should"):
        errs.append(f"{p}: enforce must be must|should")
    pat = r"^G-\d{4}$" if scope == "global" else r"^\d{4}$"
    if not re.match(pat, adr["id"]):
        errs.append(f"{p}: id `{adr['id']}` must match {pat}")
    t = adr.get("tags") or []
    if not isinstance(t, list) or not 1 <= len(t) <= 5:
        errs.append(f"{p}: tags must be a list of 1-5")
    for tag in t if isinstance(t, list) else []:
        if tag not in tags:
            errs.append(f"{p}: unknown tag `{tag}` (add it to TAGS.md)")
    aw = adr.get("applies_when")
    if aw is not None and (not isinstance(aw, list) or not all(isinstance(x, str) for x in aw)):
        errs.append(f"{p}: applies_when must be a list of glob strings")
    if adr.get("status") == "superseded" and not adr.get("superseded_by"):
        errs.append(f"{p}: superseded without superseded_by")
    for s in SECTIONS:
        if s not in adr["_sections"]:
            errs.append(f"{p}: missing section `## {s}`")
    return errs


def load_dir(d, scope):
    out = []
    if not d or not os.path.isdir(d):
        return out
    for name in sorted(os.listdir(d)):
        if name.endswith(".md") and name not in ("INDEX.md", "TAGS.md", "README.md") and not name.startswith("_"):
            out.append(parse(os.path.join(d, name)))
    for a in out:
        a["_scope_dir"] = scope
    return out


def check_links(repo, glob):
    errs, ids = [], {a["id"] for a in repo + glob}
    for a in repo + glob:
        for s in a.get("supersedes") or []:
            if str(s) not in ids:
                errs.append(f"{a['_path']}: supersedes unknown id `{s}`")
        if a.get("superseded_by") and str(a["superseded_by"]) not in ids:
            errs.append(f"{a['_path']}: superseded_by unknown id `{a['superseded_by']}`")
    return errs


def render_index(adrs):
    adrs = sorted(adrs, key=lambda a: (0 if a.get("scope") == "repo" else 1, a["id"]))
    lines = [
        "<!-- generated by adr-index.sh; do not edit -->",
        "| id | status | enforce | tags | decision |",
        "| --- | --- | --- | --- | --- |",
    ]
    for a in adrs:
        decision = a["_sections"].get("Decision", "").splitlines()[0] if a["_sections"].get("Decision") else a["title"]
        lines.append(f"| {a['id']} | {a['status']} | {a['enforce']} | {','.join(a['tags'])} | {decision} |")
    return "\n".join(lines) + "\n"


def find_repo_adr_dir(start):
    d = os.path.abspath(start)
    while True:
        for cand in ("docs/adr", "docs/adrs", "adr"):
            p = os.path.join(d, cand)
            if os.path.isdir(p) and os.path.realpath(p) != os.path.realpath(GLOBAL_DIR):
                return p
        if os.path.isdir(os.path.join(d, ".git")) or os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def cmd_index(args):
    d = os.path.abspath(args.dir)
    scope = "global" if os.path.realpath(d) == os.path.realpath(GLOBAL_DIR) else "repo"
    tags = load_tags()
    try:
        adrs = load_dir(d, scope)
        glob = adrs if scope == "global" else load_dir(GLOBAL_DIR, "global")
    except AdrError as e:
        print(f"adr-index: {e}", file=sys.stderr)
        return 2
    errs = [e for a in adrs for e in validate(a, tags, scope)]
    errs += check_links(adrs if scope == "repo" else [], glob)
    if errs:
        print("adr-index: invalid ADRs:\n  " + "\n  ".join(errs), file=sys.stderr)
        return 2
    want = render_index(adrs)
    path = os.path.join(d, "INDEX.md")
    have = open(path).read() if os.path.exists(path) else ""
    if args.check:
        if have != want:
            print(f"adr-index: {path} is stale; run: adr-index.sh {d}", file=sys.stderr)
            return 1
        print(f"adr-index: {path} ok ({len(adrs)} ADRs)")
        return 0
    if have != want:
        with open(path, "w") as f:
            f.write(want)
    print(f"adr-index: wrote {path} ({len(adrs)} ADRs)")
    return 0


def infer_tags(files):
    out = set()
    for f in files:
        for pat, t in FILE_TAGS:
            if fnmatch.fnmatch(f, pat) or fnmatch.fnmatch(os.path.basename(f), pat):
                out.update(t)
    return out


SKIP_DIRS = {".git", "node_modules", ".terraform", "vendor", "dist", "__pycache__"}


def repo_has(root, patterns, max_files=20000):
    """True if any file under root matches one of the glob patterns (basename or relative path)."""
    n = 0
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            n += 1
            rel = os.path.relpath(os.path.join(d, f), root)
            if any(fnmatch.fnmatch(f, p) or fnmatch.fnmatch(rel, p) for p in patterns):
                return True
            if n > max_files:
                return True  # too big to scan: be conservative, keep the ADR
    return False


def cmd_resolve(args):
    tags = {t.strip() for t in (args.tags or "").split(",") if t.strip()}
    tags |= infer_tags(args.files or [])
    repo_dir = args.repo_dir or find_repo_adr_dir(os.getcwd())
    try:
        repo = load_dir(repo_dir, "repo")
        glob = load_dir(GLOBAL_DIR, "global")
    except AdrError as e:
        if args.soft:
            print(f"# ADR resolution error: {e}\n# Report this as an invalid ADR; continue without ADR constraints.")
            return 0
        print(f"adr-resolve: {e}", file=sys.stderr)
        return 2
    superseded = {str(s) for a in repo if a.get("status") == "accepted" for s in a.get("supersedes") or []}
    repo_root = os.path.dirname(os.path.dirname(repo_dir)) if repo_dir and repo_dir.rstrip("/").endswith("docs/adr") else (os.path.dirname(repo_dir) if repo_dir else os.getcwd())
    hits, not_applicable = [], []
    for a in repo + glob:
        if a.get("status") != "accepted" or not tags & set(a.get("tags") or []):
            continue
        if a["scope"] == "global" and a["id"] in superseded:
            continue
        if a.get("applies_when") and not repo_has(repo_root, a["applies_when"]):
            not_applicable.append(a["id"])
            continue
        hits.append(a)
    print(f"# ADR constraints  tags={','.join(sorted(tags)) or '-'}  repo_dir={repo_dir or 'none'}")
    if superseded:
        print(f"# superseded by repo ADRs (ignore these globals): {', '.join(sorted(superseded))}")
    if not_applicable:
        print(f"# not applicable here (applies_when unmatched; do not cite): {', '.join(not_applicable)}")
    if not hits:
        print("# none matched: no ADR constrains this task")
        return 0
    for a in hits:
        label = f"ADR-{a['id']}"
        print(f"\n## {label} [{a['enforce']}] [{a['scope']}] {a['title']}")
        if a.get("supersedes"):
            print(f"supersedes: {', '.join(str(s) for s in a['supersedes'])}")
        print("Decision: " + a["_sections"].get("Decision", ""))
        print("Rules:\n" + a["_sections"].get("Rules", ""))
        exc = a["_sections"].get("Exceptions", "")
        if exc and exc.lower() not in ("none", "none."):
            print("Exceptions: " + exc)
        if str(a.get("date", "")) and _stale(a):
            print("note: older than 18 months; follow it but flag as stale for review")
    print("\n# Apply: must = hard constraint; should = default, deviate only with a stated reason.")
    print("# Cite inline as (per ADR-<id>). Repo vs global contradiction with no supersedes link: follow repo, flag the missing link.")
    return 0


def _stale(a):
    try:
        d = a["date"] if isinstance(a["date"], dt.date) else dt.date.fromisoformat(str(a["date"]))
        return (dt.date.today() - d).days > 548
    except ValueError:
        return False


def cmd_next_id(args):
    d = os.path.abspath(args.dir)
    scope = "global" if os.path.realpath(d) == os.path.realpath(GLOBAL_DIR) else "repo"
    nums = [int(re.sub(r"\D", "", a["id"]) or 0) for a in load_dir(d, scope)]
    n = max(nums, default=0) + 1
    print(f"G-{n:04d}" if scope == "global" else f"{n:04d}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("index"); p.add_argument("dir"); p.add_argument("--check", action="store_true")
    p = sub.add_parser("resolve"); p.add_argument("--tags"); p.add_argument("--files", nargs="*"); p.add_argument("--repo-dir")
    p.add_argument("--soft", action="store_true", help="never exit non-zero (for skill-load injection)")
    p = sub.add_parser("next-id"); p.add_argument("dir")
    a = ap.parse_args()
    return {"index": cmd_index, "resolve": cmd_resolve, "next-id": cmd_next_id}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
