#!/usr/bin/env python3
"""Install / uninstall agent-config into a Claude config dir (default ~/.claude) without clobbering it.

install:   per-item symlinks (skills/*, agents/*.md, adrs), a marked @import block in CLAUDE.md,
           and a merge of settings.json. Everything added is recorded in a manifest.
uninstall: removes exactly what the manifest recorded; leaves anything else untouched.
Backups of CLAUDE.md and settings.json go to <claude-home>/backups/agent-config-<ts>/ before any change.
"""
import argparse
import copy
import datetime as dt
import json
import os
import shutil
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BEGIN = "<!-- agent-config:begin (managed by `make install` in {repo}; remove with `make uninstall`) -->"
END = "<!-- agent-config:end -->"
MANIFEST = ".agent-config-manifest.json"


def items(home):
    """(source, link) pairs this repo owns."""
    out = []
    for name in sorted(os.listdir(os.path.join(REPO, "skills"))):
        if os.path.isfile(os.path.join(REPO, "skills", name, "SKILL.md")):
            out.append((os.path.join(REPO, "skills", name), os.path.join(home, "skills", name)))
    for name in sorted(os.listdir(os.path.join(REPO, "agents"))):
        if name.endswith(".md"):
            out.append((os.path.join(REPO, "agents", name), os.path.join(home, "agents", name)))
    out.append((os.path.join(REPO, "adrs"), os.path.join(home, "adrs")))
    return out


def rendered_settings(home):
    raw = open(os.path.join(REPO, "settings.json")).read()
    raw = raw.replace("__AGENT_CONFIG__", REPO).replace("__HOME__", os.path.expanduser("~"))
    return json.loads(raw)


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        txt = f.read()
    return json.loads(txt) if txt.strip() else {}


def write_json(path, data, trailing_nl=True):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        if trailing_nl:
            f.write("\n")


def backup(home, log):
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bdir = os.path.join(home, "backups", f"agent-config-{ts}")
    os.makedirs(bdir, exist_ok=True)
    for name in ("CLAUDE.md", "settings.json"):
        p = os.path.join(home, name)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(bdir, name))
    log(f"backup   {bdir}")
    return bdir


def is_ours(link):
    return os.path.islink(link) and os.path.realpath(link).startswith(REPO + os.sep)


def install(home, dry):
    log = (lambda m: print(("[dry-run] " if dry else "") + m))
    man_path = os.path.join(home, MANIFEST)
    if os.path.exists(man_path):
        log("already installed; reinstalling (uninstall + install)")
        if not dry:
            uninstall(home, False, quiet=True)

    conflicts = [link for src, link in items(home) if os.path.lexists(link) and not is_ours(link)]
    if conflicts:
        print("conflict: these paths exist and are not agent-config symlinks; move them first:\n  " + "\n  ".join(conflicts), file=sys.stderr)
        return 1

    manifest = {"repo": REPO, "installed_at": dt.datetime.now().isoformat(timespec="seconds"),
                "symlinks": [], "created_dirs": [], "claude_md": None, "settings": {}}
    if not dry:
        manifest["backup"] = backup(home, log)

    for d in ("skills", "agents"):
        p = os.path.join(home, d)
        if not os.path.isdir(p):
            log(f"mkdir    {p}")
            manifest["created_dirs"].append(p)
            if not dry:
                os.makedirs(p)
    for src, link in items(home):
        log(f"link     {link} -> {src}")
        if not dry:
            if os.path.islink(link):
                os.unlink(link)
            os.symlink(src, link)
        manifest["symlinks"].append(link)

    # CLAUDE.md: append managed import block
    cm = os.path.join(home, "CLAUDE.md")
    existed = os.path.exists(cm)
    text = open(cm).read() if existed else ""
    block = f"{BEGIN.format(repo=REPO)}\n@{os.path.join(REPO, 'CLAUDE.md')}\n{END}\n"
    sep = "" if (not text or text.endswith("\n\n")) else ("\n" if text.endswith("\n") else "\n\n")
    manifest["claude_md"] = {"existed": existed, "sep": sep}
    log(f"append   {cm} (@import block)")
    if not dry:
        with open(cm, "w") as f:
            f.write(text + sep + block)

    # settings.json: merge permissions + hooks, record exactly what was added
    sp = os.path.join(home, "settings.json")
    cur = load_json(sp)
    s_existed = cur is not None
    cur = cur or {}
    ours = rendered_settings(home)
    trailing = open(sp).read().endswith("\n") if s_existed else True
    added = {"existed": s_existed, "trailing_nl": trailing, "created_keys": [], "permissions": {}, "hooks": {}}
    for key in ("permissions", "hooks"):
        if key not in cur:
            cur[key] = {}
            added["created_keys"].append(key)
    for kind, rules in ours["permissions"].items():
        if kind not in cur["permissions"]:
            added.setdefault("created_perm_kinds", []).append(kind)
        lst = cur["permissions"].setdefault(kind, [])
        new = [r for r in rules if r not in lst]
        lst.extend(new)
        added["permissions"][kind] = new
        log(f"settings permissions.{kind} += {len(new)}")
    for event, groups in ours["hooks"].items():
        lst = cur["hooks"].setdefault(event, [])
        new = [g for g in groups if g not in lst]
        lst.extend(new)
        added["hooks"][event] = new
        log(f"settings hooks.{event} += {len(new)} matcher group(s)")
    manifest["settings"] = added
    if not dry:
        write_json(sp, cur, trailing)
        write_json(man_path, manifest)
        log(f"manifest {man_path}")
    log("installed" if not dry else "dry-run complete; nothing changed")
    return 0


def uninstall(home, dry, quiet=False):
    log = (lambda m: None) if quiet else (lambda m: print(("[dry-run] " if dry else "") + m))
    man_path = os.path.join(home, MANIFEST)
    if not os.path.exists(man_path):
        log(f"not installed (no {man_path})")
        return 0
    man = json.load(open(man_path))

    for link in man["symlinks"]:
        if is_ours(link):
            log(f"unlink   {link}")
            if not dry:
                os.unlink(link)
        elif os.path.lexists(link):
            log(f"skip     {link} (no longer an agent-config symlink)")
    for d in reversed(man.get("created_dirs", [])):
        if os.path.isdir(d) and not [x for x in os.listdir(d) if x != ".DS_Store"]:
            log(f"rmdir    {d}")
            if not dry:
                shutil.rmtree(d)

    cm = os.path.join(home, "CLAUDE.md")
    if os.path.exists(cm):
        text = open(cm).read()
        b = text.find("<!-- agent-config:begin")
        e = text.find(END, b)
        if b != -1 and e != -1:
            e += len(END) + (1 if text[e + len(END):e + len(END) + 1] == "\n" else 0)
            sep = man["claude_md"].get("sep", "")
            start = b - len(sep) if sep and text[:b].endswith(sep) else b
            new = text[:start] + text[e:]
            log(f"strip    {cm} (@import block)")
            if not dry:
                if not new and not man["claude_md"]["existed"]:
                    os.remove(cm)
                else:
                    open(cm, "w").write(new)

    sp = os.path.join(home, "settings.json")
    cur = load_json(sp)
    if cur is not None:
        st = man["settings"]
        for kind, rules in st["permissions"].items():
            lst = cur.get("permissions", {}).get(kind)
            if lst is None:
                continue
            for r in rules:
                if r in lst:
                    lst.remove(r)
            if not lst and kind in st.get("created_perm_kinds", []):
                del cur["permissions"][kind]
        for event, groups in st["hooks"].items():
            lst = cur.get("hooks", {}).get(event)
            if lst is None:
                continue
            for g in groups:
                if g in lst:
                    lst.remove(g)
            if not lst:
                del cur["hooks"][event]
        for key in st["created_keys"]:
            if key in cur and not cur[key]:
                del cur[key]
        log(f"restore  {sp} (removed agent-config permissions + hooks)")
        if not dry:
            if not st["existed"] and not cur:
                os.remove(sp)
            else:
                write_json(sp, cur, st.get("trailing_nl", True))
    if not dry:
        os.remove(man_path)
    log("uninstalled" if not dry else "dry-run complete; nothing changed")
    return 0


def status(home):
    man_path = os.path.join(home, MANIFEST)
    if not os.path.exists(man_path):
        print(f"agent-config: not installed in {home}")
        return 1
    man = json.load(open(man_path))
    ok = all(is_ours(l) for l in man["symlinks"])
    blk = "<!-- agent-config:begin" in open(os.path.join(home, "CLAUDE.md")).read()
    print(f"agent-config: installed {man['installed_at']} from {man['repo']}")
    print(f"  symlinks {len(man['symlinks'])} {'ok' if ok else 'BROKEN'}; CLAUDE.md block {'ok' if blk else 'MISSING'}")
    print(f"  settings: " + ", ".join(f"{k}+{len(v)}" for k, v in man["settings"]["permissions"].items())
          + "; hooks " + ", ".join(f"{k}+{len(v)}" for k, v in man["settings"]["hooks"].items()))
    return 0 if ok and blk else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["install", "uninstall", "status"])
    ap.add_argument("--claude-home", default=os.path.expanduser("~/.claude"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    home = os.path.abspath(os.path.expanduser(a.claude_home))
    os.makedirs(home, exist_ok=True)
    if a.cmd == "install":
        return install(home, a.dry_run)
    if a.cmd == "uninstall":
        return uninstall(home, a.dry_run)
    return status(home)


if __name__ == "__main__":
    sys.exit(main())
