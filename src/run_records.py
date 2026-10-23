"""
Run records: per-run manifests with status lifecycle, configuration snapshot, Git state and
artifact checksums, plus their verification (see docs/reproducibility.md §4).

Lifecycle: start() writes status "running"; complete(artifacts) hashes every artifact and then
writes "completed"; fail(exc) writes "failed". A run is trusted only when its manifest is
"completed" and every artifact still matches its recorded SHA-256.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import random
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

from src.config import REPO_ROOT, resolve_path


def seed_everything(seed: int) -> None:
    """Seed Python's and NumPy's global generators (model-specific random_state is set separately)."""
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical_sha256(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


CODE_PATHS = ("src", "configs", "requirements.txt")


def git_state() -> Dict[str, Any]:
    """Current commit and whether code paths (tracked changes or untracked files) differ from it."""
    def git(*args):
        return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
    commit = git("rev-parse", "HEAD") or "unknown"
    status = git("status", "--porcelain", "--untracked-files=all", "--", *CODE_PATHS)
    return {"commit": commit, "dirty": bool(status), "dirty_paths": status.splitlines()[:50]}


def code_fingerprint() -> Dict[str, Any]:
    """
    SHA-256 of every file under the code paths, independent of Git. This identifies the exact code
    that ran even when the tree is dirty or files are untracked.
    """
    files = {}
    for root in CODE_PATHS:
        p = REPO_ROOT / root
        paths = [p] if p.is_file() else sorted(x for x in p.rglob("*") if x.is_file() and "__pycache__" not in x.parts)
        for f in paths:
            files[str(f.relative_to(REPO_ROOT)).replace("\\", "/")] = sha256_file(f)
    return {"sha256": canonical_sha256(files), "files": len(files), "per_file": files}


def _software() -> Dict[str, str]:
    from src.experiment import software_versions
    return software_versions()


def _dataset_sha(cfg: Dict[str, Any]) -> str:
    version = cfg["dataset"]["version"]
    meta = resolve_path(cfg["paths"]["processed_dir"]) / f"cropcast_analysis_{version}.meta.json"
    return json.loads(meta.read_text(encoding="utf-8"))["csv_sha256"]


class RunRecorder:
    """Writes `<runs_dir>/<run_id>/manifest.json` and tags log records with the run ID."""

    def __init__(self, cfg: Dict[str, Any], kind: str):
        self.cfg = cfg
        self.kind = kind
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.run_id = f"{kind}-{stamp}-{uuid.uuid4().hex[:8]}"
        self.dir = resolve_path(cfg["paths"]["runs_dir"]) / self.run_id
        self.manifest: Dict[str, Any] = {}

    def _write(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.dir / "manifest.json.tmp"
        tmp.write_text(json.dumps(self.manifest, indent=2, default=str) + "\n", encoding="utf-8")
        tmp.replace(self.dir / "manifest.json")

    def start(self) -> "RunRecorder":
        version = self.cfg["dataset"]["version"]
        dsha = _dataset_sha(self.cfg)
        self.manifest = {
            "run_id": self.run_id, "kind": self.kind, "status": "running", "started_at": _now(), "ended_at": None,
            "git": git_state(), "code_fingerprint_start": code_fingerprint(),
            "config_sha256": canonical_sha256(self.cfg), "config": self.cfg,
            "dataset_version": f"{version}:{dsha[:12]}", "dataset_csv_sha256": dsha,
            "software": _software(), "random_seed": self.cfg["random_seed"], "artifacts": {},
            "warnings": [], "warning_counts": {},
        }
        self._write()
        return self

    def count_warnings(self, counts: Dict[str, int]) -> None:
        """Accumulate warning tallies (category: message prefix → count) observed during the run."""
        for k, v in counts.items():
            self.manifest["warning_counts"][k] = self.manifest["warning_counts"].get(k, 0) + int(v)

    def log_record(self, record: Dict[str, Any]) -> None:
        """Append a per-model record to the shared JSONL log, tagged with this run."""
        from src.experiment import append_run
        append_run(resolve_path(self.cfg["paths"]["experiment_log"]), dict(record, run_id=self.run_id, run_kind=self.kind))

    def add_warning(self, message: str) -> None:
        self.manifest["warnings"].append(message)

    def complete(self, artifacts: Iterable[Path]) -> None:
        arts = {_artifact_key(Path(p)): sha256_file(Path(p)) for p in artifacts}
        self._close("completed", artifacts=arts)

    def fail(self, exc: BaseException) -> None:
        self._close("failed", error=f"{type(exc).__name__}: {exc}")

    def _close(self, status: str, **extra) -> None:
        end_git, end_code = git_state(), code_fingerprint()
        changed = (end_code["sha256"] != self.manifest["code_fingerprint_start"]["sha256"]
                   or end_git["commit"] != self.manifest["git"]["commit"])
        changed_files = sorted(k for k in set(end_code["per_file"]) | set(self.manifest["code_fingerprint_start"]["per_file"])
                               if end_code["per_file"].get(k) != self.manifest["code_fingerprint_start"]["per_file"].get(k))
        self.manifest.update(status=status, ended_at=_now(), git_end=end_git, code_fingerprint_end=end_code,
                             tree_changed_during_run=changed, files_changed_during_run=changed_files, **extra)
        self._write()


def write_retrospective_manifest(cfg: Dict[str, Any], kind: str, run_started: str, run_ended: str,
                                 artifacts: Iterable[Path], provenance_notes: List[str],
                                 log_records_window: Tuple[str, str]) -> Path:
    """
    Manifest for a run executed before run records existed. It is marked `retrospective: true`.
    Code identity at run time is recorded as unknown; only the artifacts' hashes at the time of
    writing and the given notes are asserted.
    """
    rec = RunRecorder(cfg, kind)
    version = cfg["dataset"]["version"]
    dsha = _dataset_sha(cfg)
    arts = {_artifact_key(Path(p)): sha256_file(Path(p)) for p in artifacts}
    rec.run_id = f"{kind}-retrospective-{run_started.replace(':', '').replace('-', '')[:15]}"
    rec.dir = resolve_path(cfg["paths"]["runs_dir"]) / rec.run_id
    rec.manifest = {
        "run_id": rec.run_id, "kind": kind, "status": "completed", "retrospective": True,
        "started_at": run_started, "ended_at": run_ended, "manifest_written_at": _now(),
        "git": {"commit": "unknown at run time", "dirty": True, "dirty_paths": []},
        "code_fingerprint_start": None, "code_fingerprint_end": None, "tree_changed_during_run": None,
        "provenance_notes": provenance_notes, "config_sha256": None, "config": None,
        "config_note": "Configuration snapshot was not captured at run time; see per-record fields in the JSONL log.",
        "dataset_version": f"{version}:{dsha[:12]}", "dataset_csv_sha256": dsha,
        "software": _software(), "random_seed": cfg["random_seed"], "artifacts": arts,
        "log_records_window": list(log_records_window), "warnings": [], "warning_counts": {},
    }
    rec._write()
    return rec.dir / "manifest.json"


def _artifact_key(p: Path) -> str:
    """Repository-relative POSIX path when inside the repository, otherwise the absolute path."""
    try:
        return str(p.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(p.resolve())


class WarningTally:
    """
    Context manager that records every warning raised inside it instead of suppressing it:
    each distinct (category, message) is counted, its first occurrence is logged, and the counts
    are written to the run manifest. Counting is thread-safe (scikit-learn warns from worker threads).
    """

    def __init__(self, recorder: "RunRecorder | None" = None, log=None):
        import collections
        import logging
        import threading
        self.recorder = recorder
        self.log = log or logging.getLogger("cropcast.warnings")
        self.counts = collections.Counter()
        self._lock = threading.Lock()

    def _show(self, message, category, filename, lineno, file=None, line=None):
        key = f"{category.__name__}: {str(message)[:160]}"
        with self._lock:
            first = key not in self.counts
            self.counts[key] += 1
        if first:
            self.log.warning("warning (first occurrence; all occurrences are counted in the run manifest): %s [%s:%s]",
                             key, filename, lineno)

    def __enter__(self) -> "WarningTally":
        import warnings
        self._cm = warnings.catch_warnings()
        self._cm.__enter__()
        warnings.simplefilter("always")
        warnings.showwarning = self._show
        return self

    def __exit__(self, *exc) -> bool:
        self._cm.__exit__(*exc)
        if self.recorder is not None:
            self.recorder.count_warnings(dict(self.counts))
        return False


def _resolve_artifact(key: str) -> Path:
    p = Path(key)
    return p if p.is_absolute() else REPO_ROOT / p


def verify_run_manifests(cfg: Dict[str, Any], kinds: Tuple[str, ...] = ("forecasting", "anomaly")) -> Tuple[bool, str]:
    """
    For each run kind: the latest run must be completed; its artifacts must exist and match their
    hashes; the configuration and dataset must be unchanged since the run; and every log record of
    the run must have a config hash that can be recomputed from its stored fields.
    """
    from src.experiment import config_hash
    runs_dir = resolve_path(cfg["paths"]["runs_dir"])
    log_path = resolve_path(cfg["paths"]["experiment_log"])
    problems: List[str] = []
    notes: List[str] = []
    records = []
    if log_path.exists():
        records = [json.loads(l) for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    for kind in kinds:
        manifests = []
        for p in runs_dir.glob(f"{kind}-*/manifest.json") if runs_dir.exists() else []:
            manifests.append(json.loads(p.read_text(encoding="utf-8")))
        if not manifests:
            problems.append(f"{kind}: no run manifests found")
            continue
        latest = max(manifests, key=lambda m: m["started_at"])
        rid = latest["run_id"]
        if latest["status"] != "completed":
            problems.append(f"{kind}: latest run {rid} is {latest['status']}" + (f" ({latest.get('error')})" if latest.get("error") else ""))
            continue
        for key, sha in latest["artifacts"].items():
            path = _resolve_artifact(key)
            if not path.exists():
                problems.append(f"{kind}/{rid}: artifact missing: {key}")
            elif sha256_file(path) != sha:
                problems.append(f"{kind}/{rid}: artifact checksum differs: {key}")
        if latest.get("retrospective"):
            notes.append(f"{kind}: latest run {rid} is RETROSPECTIVE (pre-run-record; code identity unknown)")
        elif latest["config_sha256"] != canonical_sha256(cfg):
            problems.append(f"{kind}/{rid}: configuration changed since the run")
        if latest["dataset_csv_sha256"] != _dataset_sha(cfg):
            problems.append(f"{kind}/{rid}: dataset changed since the run")
        if latest.get("tree_changed_during_run"):
            notes.append(f"{kind}/{rid}: WARNING code changed during the run: {latest.get('files_changed_during_run')}")
        elif latest.get("git", {}).get("dirty") and not latest.get("retrospective"):
            notes.append(f"{kind}/{rid}: code was not committed at run time (fingerprint "
                         f"{latest['code_fingerprint_start']['sha256'][:12]} identifies it)")
        own = [r for r in records if r.get("run_id") == rid]
        for r in own:
            if "model_params_for_hash" not in r:
                continue
            if config_hash(r["dataset_version"], r["random_seed"], r["feature_definition"], r["model_params_for_hash"]) != r["config_hash"]:
                problems.append(f"{kind}/{rid}: logged config hash cannot be recomputed for a record")
        commit = latest["git"]["commit"]
        notes.append(f"{kind}: {rid} completed at commit {commit[:10]}"
                     + (" (clean tree)" if not latest["git"].get("dirty") else " (dirty tree)")
                     + f", {len(latest['artifacts'])} artifacts verified, {len(own)} log records")
    return not problems, "; ".join(problems) if problems else "; ".join(notes)
