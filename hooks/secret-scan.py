#!/usr/bin/env python3
"""PreToolUse(Write|Edit|MultiEdit) on *.tf, *.tfvars, *.yaml, *.yml, *.json, *.env: block literal secrets.
Regex scan (gitleaks protect only scans git-staged content, which does not exist pre-write)."""
import json
import re
import sys

EXT = (".tf", ".tfvars", ".yaml", ".yml", ".json", ".env", ".hcl")
RULES = [
    (r"AKIA[0-9A-Z]{16}", "AWS access key id"),
    (r"(?i)aws_secret_access_key\s*[=:]\s*['\"]?[A-Za-z0-9/+=]{40}", "AWS secret key"),
    (r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", "private key"),
    (r"gh[pousr]_[A-Za-z0-9]{36,}", "GitHub token"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"sk-(ant-|proj-)?[A-Za-z0-9_-]{20,}", "API key"),
    (r"(?i)\b(password|passwd|secret|api_?key|token)\b\s*[=:]\s*['\"](?!\$\{|\{\{|<|CHANGEME|changeme|example|dummy|xxx)[^'\"\s]{8,}['\"]", "literal credential"),
]


def main():
    d = json.load(sys.stdin)
    ti = d.get("tool_input", {})
    path = ti.get("file_path", "")
    if not path.endswith(EXT):
        return 0
    text = "\n".join(str(x) for x in [ti.get("content"), ti.get("new_string")] + [e.get("new_string") for e in ti.get("edits", []) or []] if x)
    for pat, label in RULES:
        m = re.search(pat, text)
        if m:
            print(f"BLOCKED by agent-config secret-scan: {label} in {path} ('{m.group(0)[:12]}...'). "
                  "Use a secret reference (Secrets Manager / External Secrets / var marked sensitive), never a literal.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
