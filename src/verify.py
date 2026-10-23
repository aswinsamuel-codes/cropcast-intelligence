"""
CropCast clean-room verification: one command that runs every lightweight reproducibility check.

    python -m src.verify            # all lightweight checks (no model retraining; a few minutes)
    python -m src.verify --skip-tests
    python -m src.verify --full     # also recompute SARIMA anomaly residuals (slower)

Stages, in order:
 1 environment        Python version and installed package versions vs requirements.txt
 2 raw_inputs         offline audit of manifest, checksums and schemas (must pass)
 3 dataset_rebuild    rebuild v1 into a temp dir; bytes and SHA-256 must equal the recorded dataset
 4 unit_tests         full unittest suite
 5 run_manifests      experiment run manifests: completed status, artifact checksums, config hashes
 6 forecast_metrics   independent recomputation of metrics, DM/HLN and BH from saved predictions
 7 anomaly            independent recomputation of anomaly scores, detections and weak-label metrics
 8 report_tables      result tables in reports/final_report.md match the saved artifacts
 9 notebooks          executed notebooks have no errors and show the authoritative metrics
10 git_hygiene        no secrets or restricted data tracked; source and tests not ignored

Exit code 0 only when every stage passes. Full retraining is deliberately separate
(`python -m src.forecasting.run`, `python -m src.anomaly_detection.run`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from importlib import metadata
from pathlib import Path
from typing import Callable, List, Tuple

from src.config import REPO_ROOT, load_config, resolve_path

PY = sys.executable
Result = Tuple[bool, str]


def _run(args: List[str], timeout: int = 3600) -> subprocess.CompletedProcess:
    return subprocess.run([PY, *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout)


def stage_environment(cfg) -> Result:
    problems = []
    if sys.version_info[:2] != (3, 11):
        problems.append(f"Python {sys.version.split()[0]} (tested: 3.11)")
    for line in (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Za-z0-9_.-]+)==([^\s#]+)", line.strip())
        if not m:
            continue
        name, want = m.groups()
        try:
            have = metadata.version(name)
        except metadata.PackageNotFoundError:
            problems.append(f"{name} not installed")
            continue
        if have != want:
            problems.append(f"{name} {have} != pinned {want}")
    return not problems, "; ".join(problems) or f"Python {sys.version.split()[0]}; all pinned packages match"


def stage_raw_inputs(cfg) -> Result:
    from src.data.validate import run_audit
    audit = run_audit(manifest_path=resolve_path(cfg["paths"]["manifest"]), raw_dir=resolve_path(cfg["paths"]["raw_dir"]))
    return audit["passed"], (f"{audit['total_chunks_found']}/{audit['total_chunks_expected']} chunks; "
                             f"hard failures: {audit['hard_failures'] or 'none'}; warnings: {len(audit['warnings'])}")


def stage_dataset_rebuild(cfg) -> Result:
    from src.data.dataset import build_dataset, write_dataset
    version = cfg["dataset"]["version"]
    recorded_dir = resolve_path(cfg["paths"]["processed_dir"])
    meta = json.loads((recorded_dir / f"cropcast_analysis_{version}.meta.json").read_text(encoding="utf-8"))
    df, m = build_dataset(cfg)
    with tempfile.TemporaryDirectory() as tmp:
        csv, _ = write_dataset(df, m, Path(tmp), version)
        rebuilt = csv.read_bytes()
    sha = hashlib.sha256(rebuilt).hexdigest()
    same_bytes = rebuilt == (recorded_dir / f"cropcast_analysis_{version}.csv").read_bytes()
    ok = sha == meta["csv_sha256"] and same_bytes
    return ok, f"rebuilt SHA-256 {sha[:16]}…, recorded {meta['csv_sha256'][:16]}…, byte-identical={same_bytes}"


def stage_unit_tests(cfg) -> Result:
    p = _run(["-m", "unittest", "discover", "-s", "tests"])
    tail = p.stderr.strip().splitlines()
    ran = next((l for l in tail if l.startswith("Ran ")), "no summary")
    status = tail[-1] if tail else ""
    return p.returncode == 0, f"{ran}; {status}"


def stage_run_manifests(cfg) -> Result:
    from src.experiment import verify_run_manifests
    return verify_run_manifests(cfg)


def stage_forecast_metrics(cfg) -> Result:
    p = _run(["-m", "src.reporting.verify_results"])
    out = json.loads(p.stdout) if p.stdout.strip().startswith("{") else {"problems": [p.stderr[-500:]]}
    return p.returncode == 0, f"{out.get('rows_checked', 0)} model rows checked; problems: {out['problems'] or 'none'}"


def stage_anomaly(cfg, full: bool = False) -> Result:
    p = _run(["-m", "src.reporting.verify_anomaly"] + (["--full"] if full else []))
    out = json.loads(p.stdout) if p.stdout.strip().startswith("{") else {"problems": [p.stderr[-500:]]}
    return p.returncode == 0, f"{out.get('checks', 0)} checks; problems: {out['problems'] or 'none'}"


def stage_report_tables(cfg) -> Result:
    p = _run(["-m", "src.reporting.report_tables", "--check"])
    return p.returncode == 0, p.stdout.strip() or p.stderr[-300:]


def stage_notebooks(cfg) -> Result:
    import nbformat
    import pandas as pd
    problems = []
    nb_dir = REPO_ROOT / "notebooks"
    for name in ("01_data_audit.ipynb", "02_eda.ipynb", "03_forecasting.ipynb", "04_anomaly_analysis.ipynb"):
        path = nb_dir / name
        if not path.exists():
            problems.append(f"{name} missing")
            continue
        nb = nbformat.read(path, as_version=4)
        code = [c for c in nb.cells if c.cell_type == "code"]
        if any(c.get("execution_count") is None for c in code):
            problems.append(f"{name}: not fully executed")
        if any(o.get("output_type") == "error" for c in code for o in c.get("outputs", [])):
            problems.append(f"{name}: contains an error output")
    # Notebook 03 must display the authoritative test MAEs (rounded to 4 dp)
    nb3 = nb_dir / "03_forecasting.ipynb"
    if nb3.exists():
        text = json.dumps(nbformat.read(nb3, as_version=4).cells)
        m = pd.read_csv(resolve_path(cfg["paths"]["tables_dir"]) / "forecast_test_metrics.csv")
        missing = [f"{r.series_id}/{r.model}" for r in m.itertuples() if f"{round(r.mae, 4):.4f}".rstrip("0").rstrip(".") not in text]
        if missing:
            problems.append(f"03_forecasting: MAE not shown for {missing}")
    return not problems, "; ".join(problems) or "4 notebooks executed without errors; notebook 03 matches the metrics table"


def stage_git_hygiene(cfg) -> Result:
    problems = []
    tracked = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
    tracked = [t for t in tracked if t]
    allowed_data = {"data/raw/README.md", "data/processed/README.md"}
    for t in tracked:
        if t == ".env" or (t.startswith(".env") and t != ".env.example"):
            problems.append(f"secret file tracked: {t}")
        if t.startswith("data/") and t not in allowed_data and not t.endswith(".meta.json"):
            problems.append(f"data file tracked: {t}")
        if re.search(r"(__pycache__|\.ipynb_checkpoints|\.tmp$|\.pyc$)", t):
            problems.append(f"cache/temp file tracked: {t}")
    env = REPO_ROOT / ".env"
    if env.exists():
        key = next((l.split("=", 1)[1].strip().strip("'\"") for l in env.read_text(encoding="utf-8").splitlines()
                    if l.startswith("CEDA_API_KEY=")), "")
        if key:
            for t in tracked:
                p = REPO_ROOT / t
                if p.is_file() and p.stat().st_size < 50_000_000 and key.encode() in p.read_bytes():
                    problems.append(f"API key value found in tracked file {t}")
    example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    if re.search(r"^CEDA_API_KEY=\S+", example, re.M):
        problems.append(".env.example contains a non-empty key")
    code_files = [str(p.relative_to(REPO_ROOT)).replace("\\", "/") for d in ("src", "tests", "configs")
                  for p in (REPO_ROOT / d).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    ignored = subprocess.run(["git", "check-ignore", "--stdin"], cwd=REPO_ROOT, input="\n".join(code_files),
                             capture_output=True, text=True).stdout.split()
    if ignored:
        problems.append(f"source/test/config files ignored by .gitignore: {ignored[:5]}")
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "src", "tests", "configs"],
                               cwd=REPO_ROOT, capture_output=True, text=True).stdout.split()
    note = f"; untracked source files (commit them): {untracked[:5]}" if untracked else ""
    return not problems, ("; ".join(problems) or f"{len(tracked)} tracked files clean") + note


STAGES: List[Tuple[str, Callable]] = [
    ("environment", stage_environment), ("raw_inputs", stage_raw_inputs), ("dataset_rebuild", stage_dataset_rebuild),
    ("unit_tests", stage_unit_tests), ("run_manifests", stage_run_manifests), ("forecast_metrics", stage_forecast_metrics),
    ("anomaly", stage_anomaly), ("report_tables", stage_report_tables), ("notebooks", stage_notebooks),
    ("git_hygiene", stage_git_hygiene),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--full", action="store_true", help="also recompute SARIMA anomaly residuals")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--only", nargs="*", help="run only these stages")
    args = parser.parse_args()
    cfg = load_config()
    results = []
    for name, fn in STAGES:
        if (args.only and name not in args.only) or (args.skip_tests and name == "unit_tests"):
            continue
        start = time.time()
        try:
            ok, detail = fn(cfg, full=args.full) if name == "anomaly" else fn(cfg)
        except Exception as e:  # a crashing check is a failure, never a pass
            ok, detail = False, f"{type(e).__name__}: {e}"
        results.append({"stage": name, "passed": ok, "seconds": round(time.time() - start, 1), "detail": detail})
        print(f"[{'PASS' if ok else 'FAIL'}] {name:17s} ({results[-1]['seconds']}s) {detail}", flush=True)
    failed = [r["stage"] for r in results if not r["passed"]]
    print(f"\n{len(results) - len(failed)}/{len(results)} stages passed" + (f"; failed: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
