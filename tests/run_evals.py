#!/usr/bin/env python3
"""Behavior evals: run real `claude -p` sessions against the INSTALLED config.

Each case runs in a throwaway git copy of a demo repo, with the stream-json trace parsed for
skill routing, subagent use, scripts run, hook blocks, file changes, and final-answer shape.

  python3 tests/run_evals.py [--only GLOB] [--kind routing|shape|adr-conflict|safety|subagent]
                             [--model M] [--jobs N] [--repeat N] [--keep]
Results: tests/results/<timestamp>/{summary.md,results.json,<case>.trace.jsonl}
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import fnmatch
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import yaml

ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CASES = os.path.join(ROOT, "tests", "evals")


def load_cases():
    out = []
    for p in sorted(glob.glob(os.path.join(CASES, "**", "*.yaml"), recursive=True)):
        c = yaml.safe_load(open(p))
        c.setdefault("id", os.path.splitext(os.path.basename(p))[0])
        c["_path"] = os.path.relpath(p, ROOT)
        kinds = c.get("kinds") or [c.get("kind", "routing")]
        c["kinds"] = kinds
        out.append(c)
    return out


def prepare_workspace(case):
    tmp = tempfile.mkdtemp(prefix=f"eval-{case['id']}-")
    src = os.path.join(ROOT, case.get("cwd", "demos/payments-platform"))
    dst = os.path.join(tmp, os.path.basename(src))
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("pristine", "session-fixes"))
    for f in case.get("setup_files", {}) or {}:
        p = os.path.join(dst, f)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(case["setup_files"][f])
    subprocess.run("git init -q && git add -A && git -c user.email=e@e -c user.name=eval commit -qm base",
                   shell=True, cwd=dst, check=True)
    return tmp, dst


def run_claude(case, cwd, model, trace_path):
    cmd = ["claude", "-p", case["prompt"], "--output-format", "stream-json", "--verbose",
           "--no-session-persistence", "--permission-mode", case.get("permission_mode", "acceptEdits"),
           "--permission-prompts", "none", "--max-budget-usd", str(case.get("budget_usd", 2.0))]
    if model:
        cmd += ["--model", model]
    if case.get("allowed_tools"):  # per-case, test-session only; never touches global settings
        cmd += ["--allowedTools", *case["allowed_tools"]]
    t0 = time.time()
    with open(trace_path, "w") as tf:
        p = subprocess.run(cmd, cwd=cwd, stdout=tf, stderr=subprocess.PIPE, text=True,
                           stdin=subprocess.DEVNULL, timeout=case.get("timeout_s", 600))
    return p.returncode, time.time() - t0, p.stderr[-2000:]


def parse_trace(path):
    t = {"skills": [], "subagents": [], "bash": [], "tools": [], "reads": [], "blocks": [],
         "final": "", "cost": 0.0, "turns": 0, "sub_bash": [], "sub_tools": []}
    for line in open(path):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        parent = e.get("parent_tool_use_id")
        if e.get("type") == "assistant":
            for c in e["message"].get("content", []):
                if c.get("type") != "tool_use":
                    continue
                name, inp = c["name"], c.get("input", {})
                (t["sub_tools"] if parent else t["tools"]).append(name)
                if name == "Skill":
                    t["skills"].append(inp.get("skill") or inp.get("command") or "")
                elif name in ("Agent", "Task"):
                    t["subagents"].append(inp.get("subagent_type", ""))
                elif name == "Bash":
                    (t["sub_bash"] if parent else t["bash"]).append(inp.get("command", ""))
                elif name == "Read":
                    fp = inp.get("file_path", "")
                    t["reads"].append(fp)
                    m = re.search(r"skills/([^/]+)/SKILL\.md$", fp)
                    if m:
                        t["skills"].append(m.group(1))
        elif e.get("type") == "user":
            content = e.get("message", {}).get("content")
            for c in content if isinstance(content, list) else []:
                if c.get("type") == "tool_result":
                    txt = json.dumps(c.get("content"))
                    if "BLOCKED by agent-config" in txt or "denied" in txt.lower() and "permission" in txt.lower():
                        t["blocks"].append(txt[:300])
        elif e.get("type") == "result":
            t["final"] = e.get("result", "") or ""
            t["cost"] = e.get("total_cost_usd") or 0.0
            t["turns"] = e.get("num_turns") or 0
    return t


def prose_lines(text):
    n, fence = 0, False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence or not s or s.startswith("|"):
            continue
        n += 1
    return n


def grade(case, t, ws):
    exp, fails = case.get("expect", {}), []
    final = t["final"]

    def chk(ok, msg):
        if not ok:
            fails.append(msg)

    if "routes_to" in exp:
        chk(exp["routes_to"] in t["skills"], f"routes_to {exp['routes_to']}: skills used {t['skills'] or 'none'}")
    for s in exp.get("not_routes_to", []):
        chk(s not in t["skills"], f"must not route to {s}")
    if "subagent" in exp:
        chk(exp["subagent"] in t["subagents"], f"subagent {exp['subagent']}: used {t['subagents'] or 'none'}")
    for s in exp.get("ran_script", []):
        chk(any(s in b for b in t["bash"] + t["sub_bash"]), f"ran_script {s}")
    for s in exp.get("contains", []):
        chk(s in final, f"contains {s!r}")
    for group in exp.get("contains_any", []):
        chk(any(g.lower() in final.lower() for g in group), f"contains_any {group}")
    for s in exp.get("not_contains", []):
        chk(s.lower() not in final.lower(), f"not_contains {s!r}")
    for r in exp.get("regex", []):
        chk(re.search(r, final, re.M | re.I), f"regex {r!r}")
    for r in exp.get("not_regex", []):
        chk(not re.search(r, final, re.M | re.I), f"not_regex {r!r}")
    if "first_line_regex" in exp:
        first = next((l for l in final.splitlines() if l.strip()), "")
        chk(re.search(exp["first_line_regex"], first, re.I), f"first line {first[:80]!r} !~ {exp['first_line_regex']!r}")
    if "max_prose_lines" in exp:
        n = prose_lines(final)
        chk(n <= exp["max_prose_lines"], f"prose lines {n} > {exp['max_prose_lines']}")
    if exp.get("blocked"):
        chk(t["blocks"], "expected a hook/permission block; none seen")
    for tool in exp.get("no_tool", []):
        chk(tool not in t["tools"] + t["sub_tools"], f"must not use tool {tool}")
    for pat in exp.get("bash_regex", []):
        chk(any(re.search(pat, b) for b in t["bash"] + t["sub_bash"]), f"no bash command matched {pat!r}")
    for pat in exp.get("no_bash_regex", []):
        chk(not any(re.search(pat, b) for b in t["bash"] + t["sub_bash"]), f"ran forbidden bash {pat!r}")
    for f, needles in (exp.get("file_contains") or {}).items():
        hits = glob.glob(os.path.join(ws, f), recursive=True)
        body = "\n".join(open(h).read() for h in hits if os.path.isfile(h))
        for n in needles if isinstance(needles, list) else [needles]:
            chk(re.search(n, body, re.M), f"{f} lacks /{n}/")
    for f, needles in (exp.get("file_not_contains") or {}).items():
        hits = glob.glob(os.path.join(ws, f), recursive=True)
        body = "\n".join(open(h).read() for h in hits if os.path.isfile(h))
        for n in needles if isinstance(needles, list) else [needles]:
            chk(not re.search(n, body, re.M), f"{f} contains forbidden /{n}/")
    for f in exp.get("file_exists", []):
        chk(glob.glob(os.path.join(ws, f), recursive=True), f"expected file {f}")
    for f in exp.get("file_absent", []):
        chk(not glob.glob(os.path.join(ws, f), recursive=True), f"file must not exist: {f}")
    if "files_changed_max" in exp:
        diff = subprocess.run("git status --porcelain", shell=True, cwd=ws, capture_output=True, text=True).stdout
        n = len([l for l in diff.splitlines() if l.strip()])
        chk(n <= exp["files_changed_max"], f"files changed {n} > {exp['files_changed_max']}")
    return fails


def cluster_up(ctx):
    r = subprocess.run(["kubectl", "--context", ctx, "get", "--raw", "/readyz"], capture_output=True, timeout=15)
    return r.returncode == 0


def run_case(case, model, outdir, keep, rep):
    cid = case["id"] + (f"#{rep}" if rep else "")
    if case.get("requires_context") and not cluster_up(case["requires_context"]):
        return {"id": cid, "case": case["id"], "skill": case.get("skill"), "kinds": case["kinds"], "pass": True, "skipped": True,
                "fails": [f"SKIPPED: context {case['requires_context']} unreachable (make lab-up)"], "secs": 0, "cost": 0,
                "skills": [], "subagents": [], "final": ""}
    tmp, ws = prepare_workspace(case)
    trace = os.path.join(outdir, f"{cid.replace('#', '_')}.trace.jsonl")
    try:
        rc, secs, err = run_claude(case, ws, model, trace)
        t = parse_trace(trace)
        fails = grade(case, t, ws)
        if rc != 0 and not t["final"]:
            fails.append(f"claude exit {rc}: {err.strip()[-300:]}")
        diff = subprocess.run("git diff; git status --porcelain", shell=True, cwd=ws, capture_output=True, text=True).stdout
        open(trace.replace(".trace.jsonl", ".diff"), "w").write(diff)
        return {"id": cid, "case": case["id"], "skill": case.get("skill"), "kinds": case["kinds"], "pass": not fails,
                "fails": fails, "secs": round(secs, 1), "cost": round(t["cost"], 4), "skills": t["skills"],
                "subagents": t["subagents"], "final": t["final"]}
    finally:
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="*")
    ap.add_argument("--kind")
    ap.add_argument("--skill")
    ap.add_argument("--model", default=os.environ.get("EVAL_MODEL"))
    ap.add_argument("--jobs", type=int, default=int(os.environ.get("EVAL_JOBS", 4)))
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(os.path.expanduser("~/.claude/.agent-config-manifest.json")):
        print("agent-config is not installed; run `make install` first (evals test the installed config).", file=sys.stderr)
        return 2
    cases = [c for c in load_cases() if fnmatch.fnmatch(c["id"], a.only)
             and (not a.kind or a.kind in c["kinds"]) and (not a.skill or c.get("skill") == a.skill)]
    if a.list:
        for c in cases:
            print(f"{c['id']:40} {c.get('skill', ''):18} {','.join(c['kinds'])}")
        return 0
    outdir = os.path.join(ROOT, "tests", "results", dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    os.makedirs(outdir, exist_ok=True)
    jobs = [(c, r) for c in cases for r in range(a.repeat)]
    print(f"running {len(jobs)} eval run(s), {a.jobs} parallel, model={a.model or 'default'} -> {os.path.relpath(outdir, ROOT)}")
    results = []
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        futs = {ex.submit(run_case, c, a.model, outdir, a.keep, r if a.repeat > 1 else 0): c for c, r in jobs}
        for f in cf.as_completed(futs):
            try:
                r = f.result()
            except Exception as e:
                c = futs[f]
                r = {"id": c["id"], "case": c["id"], "skill": c.get("skill"), "kinds": c["kinds"], "pass": False,
                     "fails": [f"runner error: {e}"], "secs": 0, "cost": 0, "skills": [], "subagents": [], "final": ""}
            results.append(r)
            print(f"{'SKIP' if r.get('skipped') else 'PASS' if r['pass'] else 'FAIL'}  {r['id']:40} {r['secs']:>6}s ${r['cost']:<7} " + ("; ".join(r["fails"]))[:220])
    results.sort(key=lambda r: r["id"])
    json.dump(results, open(os.path.join(outdir, "results.json"), "w"), indent=2)
    passed = sum(r["pass"] for r in results)
    lines = [f"# Eval run {os.path.basename(outdir)}", "", f"{passed}/{len(results)} passed, cost ${sum(r['cost'] for r in results):.2f}", "",
             "| case | skill | kinds | result | skills used | subagents | failures |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in results:
        lines.append(f"| {r['id']} | {r['skill']} | {','.join(r['kinds'])} | {'PASS' if r['pass'] else 'FAIL'} | "
                     f"{','.join(r['skills'])} | {','.join(r['subagents'])} | {'; '.join(r['fails']).replace('|', '/')} |")
    open(os.path.join(outdir, "summary.md"), "w").write("\n".join(lines) + "\n")
    print(f"\n{passed}/{len(results)} passed; total ${sum(r['cost'] for r in results):.2f}; summary: {os.path.relpath(outdir, ROOT)}/summary.md")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
