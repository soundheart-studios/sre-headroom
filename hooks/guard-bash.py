#!/usr/bin/env python3
"""PreToolUse(Bash) guard: destructive-command denylist + prod gate.

Permission deny rules match prefixes, so `kubectl --context x delete ...` or
`cd envs/prod && terraform apply` slip past them. This hook parses every segment.
Exit 2 + stderr = block (shown to the agent). Exit 0 = allow.
"""
import json
import os
import re
import shlex
import subprocess
import sys

DESTRUCTIVE = [
    (r"\bterraform\b.*\b(apply|destroy)\b", "terraform apply/destroy"),
    (r"\bterraform\b.*\bstate\s+(rm|push|replace-provider)\b", "terraform state rm/push"),
    (r"\btofu\b.*\b(apply|destroy)\b", "tofu apply/destroy"),
    (r"\bkubectl\b.*\s(delete|drain)\b", "kubectl delete/drain"),
    (r"\bhelm\b.*\s(uninstall|delete)\b", "helm uninstall"),
    (r"\baws\b.*\s(delete-[\w-]+|terminate-instances|rb|purge-queue)\b", "aws delete/terminate"),
    (r"\baws\s+s3\s+rm\b.*--recursive", "aws s3 rm --recursive"),
    (r"\bgcloud\b.*\sdelete\b", "gcloud delete"),
    (r"\baz\b.*\sdelete\b", "az delete"),
]
# Any command aimed at prod needs the word "prod" in the latest user turn.
PROD = r"(--context[= ]\S*prod|--kube-context[= ]\S*prod|AWS_PROFILE=\S*prod|--profile[= ]\S*prod|envs/prod\b|workspace\s+select\s+prod|-chdir=\S*prod|\bprod-[\w-]*cluster|\bctx-prod)"


def segments(cmd):
    return [s.strip() for s in re.split(r"&&|\|\||;|\|(?!\|)|\n", cmd) if s.strip()]


def last_user_text(transcript_path):
    """Text of the most recent human turn (not tool results)."""
    if not transcript_path or not os.path.exists(transcript_path):
        return ""
    last = ""
    with open(transcript_path) as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") != "user" or e.get("isMeta"):
                continue
            c = e.get("message", {}).get("content")
            if isinstance(c, str):
                last = c
            elif isinstance(c, list):
                txt = " ".join(p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text")
                if txt.strip():
                    last = txt
    return last


def current_kube_context():
    try:
        r = subprocess.run(["kubectl", "config", "current-context"], capture_output=True, text=True, timeout=3)
        return r.stdout.strip()
    except Exception:
        return ""


def block(msg):
    print(f"BLOCKED by agent-config guard-bash: {msg}", file=sys.stderr)
    sys.exit(2)


def strip_heredocs(cmd):
    """Heredoc bodies are file content, not commands: `cat > f <<'E' ... E` must not trip the guard."""
    return re.sub(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2\s*(?=\n|$)", "<<HEREDOC", cmd, flags=re.S)


def main():
    data = json.load(sys.stdin)
    cmd = strip_heredocs(data.get("tool_input", {}).get("command", ""))
    for seg in segments(cmd):
        try:
            norm = " ".join(shlex.split(seg))
        except ValueError:
            norm = seg
        if norm.startswith(("echo ", "printf ", "#")):
            continue
        for pat, label in DESTRUCTIVE:
            if re.search(pat, norm):
                block(f"{label} is denied for agents. Output the command for the user to run instead; do not retry a variant.")
    infra = [s for s in segments(cmd) if re.search(r"\b(kubectl|helm|terraform|tofu|aws|gcloud|az)\b", s)]
    if not infra and re.search(r"\bcd\b\s+\S*prod", cmd):  # `cd envs/prod && terraform ...` split across segments
        infra = [cmd]
    targets_prod = infra and re.search(PROD, cmd if re.search(r"\bcd\b", cmd) else " ".join(infra), re.I)
    if not targets_prod and re.search(r"\b(kubectl|helm)\b", cmd) and "--context" not in cmd and "--kube-context" not in cmd:
        targets_prod = "prod" in current_kube_context().lower()
    if targets_prod and not re.search(r"\bprod(uction)?\b", last_user_text(data.get("transcript_path")), re.I):
        block("command targets prod but the user's request does not say 'prod'. Ask: 'Confirm target env: prod?'")
    sys.exit(0)


if __name__ == "__main__":
    main()
