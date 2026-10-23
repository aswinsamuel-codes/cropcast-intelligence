"""
Experiment provenance (Req 10.3-10.5): configuration hash and append-only JSONL run log.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import platform
from pathlib import Path
from typing import Any, Dict, Iterable


class IncompleteConfigError(ValueError):
    """Raised when a run would use parameters not fully specified in configuration."""


def require_keys(section: Dict[str, Any], keys: Iterable[str], where: str) -> None:
    missing = [k for k in keys if k not in section]
    if missing:
        raise IncompleteConfigError(f"{where}: missing required configuration keys {missing}")


def config_hash(dataset_version: str, seed: int, feature_definition: Dict[str, Any], model_params: Dict[str, Any]) -> str:
    """SHA-256 over a canonical JSON encoding of everything that determines a run's results."""
    payload = {"dataset_version": dataset_version, "random_seed": seed,
               "feature_definition": feature_definition, "model_params": model_params}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def software_versions() -> Dict[str, str]:
    import numpy
    import pandas
    import scipy
    import sklearn
    import statsmodels
    return {"python": platform.python_version(), "numpy": numpy.__version__, "pandas": pandas.__version__,
            "scipy": scipy.__version__, "scikit-learn": sklearn.__version__, "statsmodels": statsmodels.__version__}


def append_run(log_path: Path, record: Dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = dict(record, logged_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


# Run records live in src/run_records.py; re-exported here as the experiment API
from src.run_records import (  # noqa: E402,F401
    RunRecorder, WarningTally, code_fingerprint, git_state, seed_everything, verify_run_manifests,
    write_retrospective_manifest,
)
