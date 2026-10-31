#!/usr/bin/env python3
"""Deterministic tests for scripts, hooks, validator, and installer (no model calls).
Covers script exit codes, hook decisions, validator mutations, and install round-trips."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ADR = os.path.join(ROOT, "skills/_adr/scripts")
PAY = os.path.join(ROOT, "demos/payments-platform")


def run(cmd, stdin=None, cwd=ROOT, env=None):
    return subprocess.run(cmd, input=stdin, capture_output=True, text=True, cwd=cwd, shell=isinstance(cmd, str),
                          env={**os.environ, **(env or {})})


def sub(path, old, new):
    txt = open(path).read()
    assert old in txt, (path, old)
    with open(path, "w") as f:
        f.write(txt.replace(old, new))


def hook(script, payload):
    exe = ["python3", script] if script.endswith(".py") else [script]
    return run(exe, stdin=json.dumps(payload))


class Repo(unittest.TestCase):
    """Copy of the repo for mutation tests."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, "repo")
        shutil.copytree(ROOT, self.repo, ignore=shutil.ignore_patterns("results", ".git"), symlinks=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def validate(self):
        return run(["python3", "ci/validate.py"], cwd=self.repo)


class TestPlanSummary(unittest.TestCase):
    S = os.path.join(ROOT, "skills/terraform/scripts/plan-summary.sh")

    def test_replace_exits_4(self):
        r = run([self.S, f"{PAY}/fixtures/plan-replace.json"])
        self.assertEqual(r.returncode, 4)
        self.assertIn("replace\taws_db_instance.ledger", r.stdout)
        self.assertIn("aws_iam_policy.worker", r.stdout.split("== flagged")[1])

    def test_clean_exits_0(self):
        self.assertEqual(run([self.S, f"{PAY}/fixtures/plan-clean.json"]).returncode, 0)

    def test_bad_input_exits_2(self):
        self.assertEqual(run([self.S, "/nonexistent.json"]).returncode, 2)


class TestAdr(Repo):
    def test_global_and_demo_indexes_fresh(self):
        for d in ["adrs", "demos/payments-platform/docs/adr", "demos/inventory-svc/docs/adr"]:
            self.assertEqual(run([f"{ADR}/adr-index.sh", os.path.join(ROOT, d), "--check"]).returncode, 0, d)

    def test_stale_index_exits_1(self):
        idx = os.path.join(self.repo, "adrs/INDEX.md")
        open(idx, "a").write("| junk |\n")
        r = run([os.path.join(self.repo, "skills/_adr/scripts/adr-index.sh"), os.path.join(self.repo, "adrs"), "--check"])
        self.assertEqual(r.returncode, 1)

    def test_unknown_tag_exits_2(self):
        p = os.path.join(self.repo, "adrs/G-0006-structured-logs.md")
        sub(p, "tags: [observability, code]", "tags: [observability, vibes]")
        r = run([os.path.join(self.repo, "skills/_adr/scripts/adr-index.sh"), os.path.join(self.repo, "adrs"), "--check"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("unknown tag `vibes`", r.stderr)

    def test_superseded_without_link_exits_2(self):
        p = os.path.join(self.repo, "adrs/G-0006-structured-logs.md")
        sub(p, "status: accepted", "status: superseded")
        r = run([os.path.join(self.repo, "skills/_adr/scripts/adr-index.sh"), os.path.join(self.repo, "adrs")])
        self.assertEqual(r.returncode, 2)

    def test_repo_overrides_global(self):
        r = run([f"{ADR}/adr-resolve.sh", "--tags", "k8s,helm"], cwd=PAY)
        self.assertIn("ADR-0002", r.stdout)
        self.assertNotIn("ADR-G-0004", r.stdout)
        self.assertIn("ADR-G-0003", r.stdout)
        self.assertLess(r.stdout.index("ADR-0002"), r.stdout.index("ADR-G-0003"))  # repo first

    def test_only_accepted_counts(self):
        r = run([f"{ADR}/adr-resolve.sh", "--tags", "messaging"], cwd=os.path.join(ROOT, "demos/inventory-svc"))
        self.assertNotIn("ADR-0002", r.stdout)

    def test_infer_tags_from_files(self):
        r = run([f"{ADR}/adr-resolve.sh", "--files", "envs/dev/main.tf"], cwd=PAY)
        self.assertIn("ADR-G-0002", r.stdout)

    def test_applies_when_skips_irrelevant_globals(self):
        lab = run([f"{ADR}/adr-resolve.sh", "--tags", "security,iam,storage"], cwd=os.path.join(ROOT, "demos/kind-lab"))
        self.assertNotIn("## ADR-G-0001", lab.stdout)
        self.assertIn("not applicable here", lab.stdout)
        pay = run([f"{ADR}/adr-resolve.sh", "--tags", "security,iam,storage"], cwd=PAY)
        self.assertIn("## ADR-G-0001", pay.stdout)
        self.assertIn("## ADR-G-0007", pay.stdout)

    def test_next_id(self):
        self.assertEqual(run([f"{ADR}/adr-next-id.sh", f"{PAY}/docs/adr"]).stdout.strip(), "0004")
        self.assertEqual(run([f"{ADR}/adr-next-id.sh", f"{ROOT}/adrs"]).stdout.strip(), "G-0008")


class TestHooks(unittest.TestCase):
    G = os.path.join(ROOT, "hooks/guard-bash.py")

    def bash(self, cmd, user_text=None):
        payload = {"tool_input": {"command": cmd}}
        if user_text is not None:
            tdir = tempfile.mkdtemp()
            tp = os.path.join(tdir, "t.jsonl")
            open(tp, "w").write(json.dumps({"type": "user", "message": {"role": "user", "content": user_text}}) + "\n")
            payload["transcript_path"] = tp
        return hook(self.G, payload).returncode

    def test_destructive_blocked(self):
        for c in ["terraform apply", "terraform -chdir=envs/dev apply -auto-approve", "terraform destroy",
                  "terraform state rm aws_s3_bucket.x", "kubectl delete pod x -n a", "kubectl --context dev -n a delete pod x",
                  "kubectl drain node1", "helm uninstall r", "aws s3api delete-bucket --bucket x",
                  "aws ec2 terminate-instances --instance-ids i-1", "gcloud compute instances delete x",
                  "cd envs/dev && terraform apply"]:
            self.assertEqual(self.bash(c), 2, c)

    def test_safe_allowed(self):
        for c in ["terraform -chdir=envs/dev plan -out=tfplan", "kubectl -n a get pods", "kubectl diff -k deploy/overlays/dev",
                  "echo terraform apply", "cat envs/prod/main.tf", "jq . plan.json"]:
            self.assertEqual(self.bash(c), 0, c)

    def test_heredoc_body_ignored(self):
        self.assertEqual(self.bash("cat > f.md <<'E'\nrun kubectl --context lab-prod apply -f x\nterraform apply\nE\necho done"), 0)
        self.assertEqual(self.bash("cat > f <<E\nhi\nE\nkubectl delete pod x"), 2)

    def test_prod_gate(self):
        self.assertEqual(self.bash("terraform -chdir=envs/prod plan", "plan the live env"), 2)
        self.assertEqual(self.bash("terraform -chdir=envs/prod plan", "plan prod please"), 0)
        self.assertEqual(self.bash("kubectl --context=eks-prod -n payments get pods", "check the pods"), 2)
        self.assertEqual(self.bash("kubectl --context=eks-prod -n payments get pods", "check the pods in production"), 0)

    def test_secret_scan(self):
        S = os.path.join(ROOT, "hooks/secret-scan.py")
        bad = {"tool_input": {"file_path": "/x/main.tf", "content": 'access_key = "AKIAIOSFODNN7EXAMPLE"'}}
        self.assertEqual(hook(S, bad).returncode, 2)
        bad2 = {"tool_input": {"file_path": "/x/v.yaml", "new_string": 'password: "hunter2hunter2"'}}
        self.assertEqual(hook(S, bad2).returncode, 2)
        ok = {"tool_input": {"file_path": "/x/main.tf", "content": "password = var.db_password"}}
        self.assertEqual(hook(S, ok).returncode, 0)
        self.assertEqual(hook(S, {"tool_input": {"file_path": "/x/a.py", "content": 'k="AKIAIOSFODNN7EXAMPLE"'}}).returncode, 0)


class TestAdrCheckHook(Repo):
    def test_stale_index_blocks_edit(self):
        H = os.path.join(self.repo, "hooks/adr-check.sh")
        pay = os.path.join(self.repo, "demos/payments-platform")
        os.makedirs(os.path.join(pay, ".git"))
        p = {"cwd": pay, "tool_input": {"file_path": f"{pay}/app/x.py"}}
        self.assertEqual(hook(H, p).returncode, 0)
        open(os.path.join(pay, "docs/adr/INDEX.md"), "a").write("x\n")
        r = hook(H, p)
        self.assertEqual(r.returncode, 2)
        self.assertIn("Regenerate", r.stderr)
        # editing an ADR file itself is allowed so the agent can fix it
        self.assertEqual(hook(H, {"cwd": pay, "tool_input": {"file_path": f"{pay}/docs/adr/0004-x.md"}}).returncode, 0)


class TestValidator(Repo):
    def test_clean_repo_passes(self):
        self.assertEqual(self.validate().returncode, 0, self.validate().stdout)

    def test_duplicated_rule_fails(self):
        p = os.path.join(self.repo, "skills/code-change/SKILL.md")
        open(p, "a").write("\n- Exact flags, versions, namespaces, resource addresses. If unsure of one: state the uncertainty\n")
        self.assertIn("duplicated rule", self.validate().stdout)

    def test_overlapping_description_fails(self):
        p = os.path.join(self.repo, "skills/code-change/SKILL.md")
        src = open(os.path.join(self.repo, "skills/terraform/SKILL.md")).read()
        desc = [l for l in src.splitlines() if l.startswith("description:")][0]
        old = [l for l in open(p).read().splitlines() if l.startswith("description:")][0]
        sub(p, old, desc)
        self.assertIn("description overlap", self.validate().stdout)

    def test_unknown_tag_fails(self):
        p = os.path.join(self.repo, "demos/payments-platform/docs/adr/0001-kafka-over-sqs.md")
        sub(p, "tags: [eda, messaging, aws]", "tags: [eda, kafkaesque]")
        self.assertIn("unknown tag", self.validate().stdout)

    def test_repo_cannot_weaken_global_deny(self):
        p = os.path.join(self.repo, "demos/payments-platform/.claude/settings.json")
        json.dump({"permissions": {"allow": ["Bash(terraform apply:*)"]}}, open(p, "w"))
        self.assertIn("weakens global deny", self.validate().stdout)

    def test_orphan_reference_fails(self):
        open(os.path.join(self.repo, "skills/terraform/references/orphan.md"), "w").write("# x\n")
        self.assertIn("orphan", self.validate().stdout)

    def test_write_tool_on_subagent_fails(self):
        p = os.path.join(self.repo, "agents/log-analyst.md")
        sub(p, "tools: Read, Grep, Glob, Bash", "tools: Read, Edit, Bash")
        self.assertIn("read-only", self.validate().stdout)


class TestInstaller(unittest.TestCase):
    def test_roundtrip_preserves_existing_config(self):
        home = tempfile.mkdtemp()
        try:
            os.makedirs(f"{home}/skills/mine")
            open(f"{home}/CLAUDE.md", "w").write("# mine\nkeep me\n")
            json.dump({"model": "opus", "permissions": {"allow": ["Bash(ls:*)"], "deny": ["Bash(rm:*)"]},
                       "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "true"}]}]}},
                      open(f"{home}/settings.json", "w"), indent=2)
            before = {f: open(f"{home}/{f}").read() for f in ("CLAUDE.md", "settings.json")}
            A = ["python3", f"{ROOT}/install/agentcfg.py"]
            self.assertEqual(run(A + ["install", "--claude-home", home]).returncode, 0)
            self.assertEqual(run(A + ["install", "--claude-home", home]).returncode, 0)  # idempotent
            s = json.load(open(f"{home}/settings.json"))
            self.assertIn("Bash(terraform apply:*)", s["permissions"]["deny"])
            self.assertEqual(s["permissions"]["deny"].count("Bash(terraform apply:*)"), 1)
            self.assertIn("Bash(rm:*)", s["permissions"]["deny"])
            self.assertTrue(os.path.islink(f"{home}/skills/terraform"))
            self.assertTrue(os.path.isdir(f"{home}/skills/mine"))
            self.assertIn("@" + ROOT + "/CLAUDE.md", open(f"{home}/CLAUDE.md").read())
            self.assertEqual(run(A + ["status", "--claude-home", home]).returncode, 0)
            self.assertEqual(run(A + ["uninstall", "--claude-home", home]).returncode, 0)
            after = {f: open(f"{home}/{f}").read() for f in ("CLAUDE.md", "settings.json")}
            self.assertEqual(before, after)
            self.assertFalse(os.path.lexists(f"{home}/skills/terraform"))
            self.assertFalse(os.path.exists(f"{home}/agents"))
            self.assertTrue(os.path.isdir(f"{home}/skills/mine"))
        finally:
            shutil.rmtree(home)

    def test_conflict_refuses(self):
        home = tempfile.mkdtemp()
        try:
            os.makedirs(f"{home}/skills/terraform")
            r = run(["python3", f"{ROOT}/install/agentcfg.py", "install", "--claude-home", home])
            self.assertEqual(r.returncode, 1)
            self.assertFalse(os.path.exists(f"{home}/.agent-config-manifest.json"))
        finally:
            shutil.rmtree(home)


if __name__ == "__main__":
    unittest.main(verbosity=1)
