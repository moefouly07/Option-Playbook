"""
End-to-end simulation of the SCANNER-V1.1 live pipeline (T1c gate).

Runs scanner/src/muse/run_scan_v11.py in a throw-away local clone against a
FAKE skill CLI that serves synthetic fixture bars. No network, no vendor
data, no effect on the real repository. Usage, from the repository root:

    python scanner/tests/pipeline_sim/run_pipeline_sim.py

The working-tree scanner/ directory is copied into the clone and committed
there, so this works both before and after the pipeline files are committed.
Exit 0 = every scenario behaved as required.
"""
import csv
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SPEC_FILES = ["scanner/SCANNER_V1_1_SPEC.md", "scanner/OUTPUT_SCHEMA.json"]
EXECUTED = ["scanner/src/muse/run_scan_v11.py", "scanner/src/muse/data_adapter.py",
            "scanner/src/muse/scanner_v11.py", "scanner/tools/implementation_ref.py"]
AS_OF = "2026-10-09"

# NYSE 2026 schedule the rule-based calendar must reproduce
CLOSED_2026 = ["2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
               "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25"]
OPEN_2026 = ["2026-10-12", "2026-11-11", "2026-11-27", "2026-12-24", "2026-07-02"]
EARLY_2026 = ["2026-11-27", "2026-12-24"]


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, check=True).stdout.strip()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="scanner_sim_"))
    repo = tmp / "repo"
    results = []

    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    try:
        subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(ROOT), str(repo)],
                       check=True)
        shutil.rmtree(repo / "scanner")
        shutil.copytree(ROOT / "scanner", repo / "scanner",
                        ignore=shutil.ignore_patterns("__pycache__", "runs"))
        git(repo, "add", "-A")
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=sim", "-c",
                        "user.email=sim@local", "commit", "-q", "--allow-empty",
                        "-m", "sim snapshot"], check=True)

        runner = repo / "scanner/src/muse/run_scan_v11.py"
        adapter = load_module(repo / "scanner/src/muse/data_adapter.py", "sim_adapter")
        tool = load_module(repo / "scanner/tools/implementation_ref.py", "sim_ref")
        ref_rules = load_module(repo / "scanner/reference/scanner_rules.py", "sim_ref_rules")
        os.environ["FAKE_REPO"] = str(repo)
        fake = load_module(HERE / "fake_skill_cli.py", "sim_fake")

        # S0 calendar
        bad = [d for d in CLOSED_2026 if adapter.is_trading_day(date.fromisoformat(d))]
        bad += [d for d in OPEN_2026 if not adapter.is_trading_day(date.fromisoformat(d))]
        bad += [d for d in EARLY_2026 if not adapter.is_early_close(date.fromisoformat(d))]
        check("S0 NYSE 2026 calendar", not bad, ", ".join(bad))

        lines = sorted(f"{p}  {tool.file_sha256(repo / p)}\n" for p in EXECUTED)
        impl_ref = "sha256:" + hashlib.sha256("".join(lines).encode()).hexdigest()
        spec_sha = git(repo, "log", "-1", "--format=%H", "--", *SPEC_FILES)

        env = dict(os.environ, ALPACA_SKILL_CLI=str(HERE / "fake_skill_cli.py"),
                   FAKE_REPO=str(repo))

        def run(*extra, scenario="normal", spec=None, impl=None, run_type="IN_SAMPLE_REPLAY",
                as_of=AS_OF, out="report.json", log="log.csv"):
            e = dict(env, FAKE_SCENARIO=scenario)
            cmd = [sys.executable, str(runner), "--run-type", run_type, "--as-of", as_of,
                   "--accepted-spec-sha", spec or spec_sha,
                   "--accepted-impl-ref", impl or impl_ref,
                   "--out", str(tmp / out), "--outcome-log", str(tmp / log), *extra]
            p = subprocess.run(cmd, capture_output=True, text=True, env=e, cwd=repo)
            rep = None
            if p.returncode == 0 and (tmp / out).is_file():
                rep = json.loads((tmp / out).read_text())
            return p.returncode, p.stderr, rep

        # expected labels from the REFERENCE implementation on the same bars
        def expected_labels():
            e = dict(env, FAKE_SCENARIO="normal")
            p = subprocess.run([sys.executable, str(HERE / "fake_skill_cli.py"),
                                "--symbols", ",".join(fake.MAP), "--feed", "sip",
                                "--timeframe", "1Day", "--bars", "130", "--end", AS_OF],
                               capture_output=True, text=True, env=e, check=True)
            data = json.loads(p.stdout)["symbols"]
            bars = {s: [ref_rules.Bar(b["t_et"][:10], float(b["o"]), float(b["h"]),
                                      float(b["l"]), float(b["c"]), float(b["v"]))
                        for b in node["bars"]] for s, node in data.items()}
            res = [ref_rules.classify(s, bars[s], bars["SPY"]) for s in bars]
            sel = ref_rules.select(res, bars)
            return {r.symbol: r.label for r in res}, sel["shortlist"]

        code, err, rep = run()
        exp_labels, exp_short = expected_labels()
        got = {r["symbol"]: r["label"] for r in rep["results"]} if rep else {}
        check("S1 replay runs, labels == reference", code == 0 and got == exp_labels,
              f"exit {code} {err.strip()[-160:]}")
        check("S1 shortlist == reference", rep is not None and rep["selection"]["shortlist"] == exp_short,
              str(rep and rep["selection"]["shortlist"]))
        check("S1 report fields", rep is not None and rep["implementation_ref"] == impl_ref
              and rep["spec_commit_sha"] == spec_sha and rep["outcome_log_rows_written"] == 21,
              "")

        code, err, rep = run(log="log.csv")
        rows = list(csv.DictReader(open(tmp / "log.csv")))
        check("S2 repeat run appends nothing", code == 0 and rep["outcome_log_rows_written"] == 0
              and len(rows) == 21, f"rows={len(rows)}")

        code, err, _ = run(spec="0" * 40)
        check("S3 wrong spec SHA refused", code == 2, err.strip()[-120:])
        code, err, _ = run(impl="sha256:" + "0" * 64)
        check("S4 wrong implementation_ref refused", code == 2, err.strip()[-120:])
        code, err, _ = run(scenario="stale_all", log="l3.csv")
        check("S5 stale SPY refused", code == 2 and "stale" in err, err.strip()[-120:])
        code, err, rep = run(scenario="stale_one", log="l4.csv")
        mu = rep and next(r for r in rep["results"] if r["symbol"] == "MU")
        check("S6 stale MU -> INSUFFICIENT_DATA + noted", code == 0 and mu["label"] == "INSUFFICIENT_DATA"
              and any(x.startswith("MU:") for x in rep["data_quality"]), err.strip()[-120:])
        code, err, rep = run(scenario="dup_date", log="l5.csv")
        aapl = rep and next(r for r in rep["results"] if r["symbol"] == "AAPL")
        check("S7 duplicate date -> excluded + noted", code == 0 and aapl["label"] == "INSUFFICIENT_DATA"
              and any(x.startswith("AAPL: excluded") for x in rep["data_quality"]), err.strip()[-120:])
        code, err, _ = run(run_type="LIVE", as_of="2026-10-09", log="l6.csv")
        check("S8 LIVE with past --as-of refused", code == 2, err.strip()[-120:])

        (repo / "NOTES.md").write_text("unrelated\n")
        git(repo, "add", "NOTES.md")
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=sim", "-c", "user.email=sim@local",
                        "commit", "-q", "-m", "unrelated"], check=True)
        code, err, _ = run(log="l7.csv")
        check("S9 unrelated commit does not block", code == 0, err.strip()[-120:])

        rules = repo / "scanner/src/muse/scanner_v11.py"
        rules.write_text(rules.read_text().replace('"zone_atr_mult": 0.5', '"zone_atr_mult": 0.9'))
        code, err, _ = run(log="l8.csv")
        check("S10 uncommitted rule change refused", code == 2, err.strip()[-120:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    width = max(len(n) for n, _, _ in results)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name:<{width}}  {'' if ok else detail}")
    failed = sum(not ok for _, ok, _ in results)
    print(f"{len(results) - failed}/{len(results)} scenarios passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
