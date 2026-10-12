"""SCANNER-V1.1 shared gates (D-022).

Used by every entry point (run_scan_v11.py, outcome_tools.py,
scheduled_job.py) so a run is refused the same way everywhere:

- spec gate:   last commit that changed the spec or schema must equal the
               accepted spec SHA (unrelated commits do not move it)
- clean tree:  no uncommitted changes to tracked files under scanner/
- manifest:    implementation_ref over PIPELINE_FILES must equal the
               accepted value

Also provides the single clock (now_et). A simulated clock is honoured ONLY
when SCANNER_SIM_NOW is set AND the skill CLI in use lives inside
scanner/tests/ (the fake CLI used by pipeline_sim). Real runs always use the
real clock.

Standard library only. No network. No credentials. No trading.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]  # scanner/src/muse/<this file> -> repo root

SPEC_FILES = ["scanner/SCANNER_V1_1_SPEC.md", "scanner/OUTPUT_SCHEMA.json"]

# One manifest for every entry point (D-022).
PIPELINE_FILES = [
    "scanner/src/muse/data_adapter.py",
    "scanner/src/muse/outcome_tools.py",
    "scanner/src/muse/pipeline_gates.py",
    "scanner/src/muse/run_scan_v11.py",
    "scanner/src/muse/scanner_v11.py",
    "scanner/src/muse/scheduled_job.py",
    "scanner/tools/implementation_ref.py",
]


class GateError(RuntimeError):
    """A gate refused the run; nothing was fetched or written."""


def spec_commit_sha(repo_root: Path = REPO_ROOT) -> Optional[str]:
    if not (repo_root / "scanner" / "SCANNER_V1_1_SPEC.md").is_file():
        return None
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "log", "-1", "--format=%H", "--",
             *SPEC_FILES],
            capture_output=True, text=True, timeout=30)
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    sha = proc.stdout.strip().lower()
    return sha if re.fullmatch(r"[0-9a-f]{40}", sha) else None


def uncommitted_scanner_changes(repo_root: Path = REPO_ROOT) -> Optional[List[str]]:
    """Tracked files under scanner/ with uncommitted changes (None = unknown)."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain",
             "--untracked-files=no", "--", "scanner"],
            capture_output=True, text=True, timeout=30)
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def sha_accepted(actual: str, accepted: str) -> bool:
    accepted = accepted.strip().lower()
    if len(accepted) < 7 or not re.fullmatch(r"[0-9a-f]+", accepted):
        return False
    return actual == accepted or actual.startswith(accepted)


def _load_impl_ref_tool(repo_root: Path):
    path = repo_root / "scanner" / "tools" / "implementation_ref.py"
    spec = importlib.util.spec_from_file_location("implementation_ref", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def implementation_manifest(repo_root: Path = REPO_ROOT) -> Tuple[list, str]:
    """(implementation_files, implementation_ref) per D-019 over PIPELINE_FILES."""
    tool = _load_impl_ref_tool(repo_root)
    entries, lines = [], []
    for rel in PIPELINE_FILES:
        h = tool.file_sha256(repo_root / rel)
        entries.append({"path": rel, "sha256": h})
        lines.append(f"{rel}  {h}\n")
    lines.sort()
    entries.sort(key=lambda e: e["path"])
    ref = "sha256:" + hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
    return entries, ref


def check_all(accepted_spec_sha: str, accepted_impl_ref: str,
              repo_root: Path = REPO_ROOT) -> Tuple[str, list, str]:
    """Run every gate. Returns (spec_sha, impl_files, impl_ref) or raises."""
    actual_sha = spec_commit_sha(repo_root)
    if actual_sha is None:
        raise GateError("cannot read the spec commit SHA (no git checkout or "
                        f"no scanner/SCANNER_V1_1_SPEC.md under {repo_root})")
    if not sha_accepted(actual_sha, accepted_spec_sha):
        raise GateError(f"spec commit SHA mismatch: spec/schema last changed in "
                        f"{actual_sha}, accepted is {accepted_spec_sha}. A spec "
                        "change needs a new acceptance pass; refusing to run.")
    dirty = uncommitted_scanner_changes(repo_root)
    if dirty is None:
        raise GateError("cannot read git status for scanner/")
    if dirty:
        raise GateError("uncommitted changes under scanner/: " + "; ".join(dirty[:5]))
    files, ref = implementation_manifest(repo_root)
    if ref != accepted_impl_ref.strip().lower():
        raise GateError(f"implementation_ref mismatch: code is {ref}, "
                        f"accepted is {accepted_impl_ref}")
    return actual_sha, files, ref


def now_et(tz, skill_cli: Path) -> Tuple[datetime, bool]:
    """(current time in ET, simulated?). See module docstring."""
    sim = os.environ.get("SCANNER_SIM_NOW")
    if sim:
        tests_dir = (REPO_ROOT / "scanner" / "tests").resolve()
        try:
            inside = tests_dir in Path(skill_cli).resolve().parents
        except Exception:
            inside = False
        if inside:
            t = datetime.fromisoformat(sim)
            return (t if t.tzinfo else t.replace(tzinfo=tz)).astimezone(tz), True
    return datetime.now(tz), False
