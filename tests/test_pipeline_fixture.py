"""
End-to-end integration test on a synthetic, legally distributable fixture.

Generates raw CEDA-format chunks (with a manifest and an overlapping pilot chunk) for two
synthetic series, plus synthetic ICTD-format label files. Then, with all paths in a temp
directory, it runs:
  audit -> dataset build (twice, byte-identical) -> forecasting runner -> independent metric
  recomputation -> anomaly runner -> run manifests.
No real CEDA data is used, so a fresh user can run it without API access.
"""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import load_config

START, END = "2019-01-01", "2020-12-31"


def make_fixture(root: Path) -> dict:
    rng = np.random.default_rng(42)
    raw = root / "raw" / "ceda"
    manifest = {"manifest_version": "1.0", "series": {}}
    series = {"onion_maharashtra": (23, 27, 1200.0), "potato_uttar_pradesh": (24, 9, 900.0)}
    days = pd.date_range(START, END, freq="D")
    for sid, (cid, stid, level) in series.items():
        n = len(days)
        weekly = np.where(days.day_of_week == 6, 0.03, 0.0)
        logp = np.log(level) + np.cumsum(rng.normal(0, 0.01, n)) + weekly
        modal = np.exp(logp)
        qty = rng.integers(5000, 20000, n).astype(float)
        keep = np.ones(n, bool)
        if sid == "onion_maharashtra":
            keep[[100, 101, 400]] = False  # missing market days
        recs_p = [{"date": f"{d.date()}T00:00:00.000Z", "commodity_id": cid, "census_state_id": stid,
                   "min_price": float(m * 0.8), "max_price": float(m * 1.2), "modal_price": float(m)}
                  for d, m, k in zip(days, modal, keep) if k]
        recs_q = [{"date": f"{d.date()}T00:00:00.000Z", "commodity_id": cid, "census_state_id": stid, "quantity": float(q)}
                  for d, q, k in zip(days, qty, keep) if k]
        chunks = []
        windows = [("2019-01-01", "2019-06-30"), ("2019-07-01", "2019-12-31"),
                   ("2020-01-01", "2020-06-30"), ("2020-07-01", "2020-12-31"), ("2020-01-01", "2020-01-15")]
        for ep, recs in (("prices", recs_p), ("quantities", recs_q)):
            for a, b in windows:
                sub = [r for r in recs if a <= r["date"][:10] <= b]
                pilot = b == "2020-01-15"
                doc = sub if pilot else {"metadata": {"endpoint": ep, "from_date": a, "to_date": b, "record_count": len(sub)}, "data": sub}
                path = raw / sid / f"{ep}_{a}_{b}.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                data = json.dumps(doc, indent=2).encode()
                path.write_bytes(data)
                chunks.append({"chunk_id": f"{ep}_{a}_{b}", "endpoint": ep, "from_date": a, "to_date": b,
                               "status": "completed", "record_count": len(sub), "sha256": hashlib.sha256(data).hexdigest(),
                               "fetched_at": f"2026-01-01T00:{len(chunks):02d}:00+00:00", "is_valid": True})
        manifest["series"][sid] = {"chunks": chunks}
    (root / "raw" / "ceda_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    labels = {}
    for sid, state in (("onion_maharashtra", "MAHARASHTRA"), ("potato_uttar_pradesh", "UTTAR PRADESH")):
        p = root / f"labels_{sid}.csv"
        pd.DataFrame([{"STARTDATE": "2020-03-01", "ENDDATE": "2020-04-10", "lastMonth": "Anomaly", "lastYear": "",
                       "SameMonth": "", "MAXMINRATIO": 1.5, "STATENAME": state, "MANDINAME": "X"},
                      {"STARTDATE": "2020-08-01", "ENDDATE": "2020-08-20", "lastMonth": "", "lastYear": "Normal",
                       "SameMonth": "", "MAXMINRATIO": 1.2, "STATENAME": state, "MANDINAME": "Y"}]).to_csv(p, index=False)
        labels[sid] = str(p)
    return labels


def fixture_config(root: Path, labels: dict) -> dict:
    cfg = copy.deepcopy(load_config())
    cfg["paths"].update({
        "raw_dir": str(root / "raw" / "ceda"), "manifest": str(root / "raw" / "ceda_manifest.json"),
        "processed_dir": str(root / "processed"), "figures_dir": str(root / "figures"),
        "tables_dir": str(root / "tables"), "reports_dir": str(root / "reports"),
        "experiment_log": str(root / "experiment_log.jsonl"), "forecasts_dir": str(root / "forecasts"),
        "runs_dir": str(root / "runs"), "ictd_labels": labels,
    })
    cfg["dataset"].update({"version": "fixture", "start_date": START, "end_date": END})
    m = cfg["forecasting"]["models"]
    m["decision_tree"]["grid"] = {"max_depth": [3], "min_samples_leaf": [20]}
    m["random_forest"].update({"n_estimators": 10, "n_jobs": 1, "grid": {"max_depth": [5], "min_samples_leaf": [20], "max_features": [1.0]}})
    m["sarima"].update({"grid": {"p": [0, 1], "q": [0], "P": [0], "Q": [0]}, "top_k_by_aic": 1, "maxiter": 50})
    m["ets"]["grid"] = {"trend": [None]}
    a = cfg["anomaly"]
    a["shocks"].update({"magnitudes": [0.5], "repeats": 1, "shocks_per_run": 2})
    a["weak_labels"]["permutations"] = 50
    return cfg


class TestFixturePipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.cfg = fixture_config(cls.root, make_fixture(cls.root))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_end_to_end(self):
        from src.anomaly_detection.run import AnomalyRunner
        from src.data.dataset import build_dataset, load_dataset, write_dataset
        from src.data.validate import run_audit
        from src.experiment import verify_run_manifests
        from src.forecasting.run import Runner

        cfg, root = self.cfg, self.root
        audit = run_audit(manifest_path=Path(cfg["paths"]["manifest"]), raw_dir=Path(cfg["paths"]["raw_dir"]),
                          start_date=START, end_date=END, chunk_months=6,
                          series_specs=[("onion_maharashtra", 23, 27), ("potato_uttar_pradesh", 24, 9)])
        self.assertTrue(audit["passed"], audit["hard_failures"])

        # Dataset: built twice, byte-identical, pilot excluded, gaps preserved
        shas = []
        for _ in range(2):
            df, meta = build_dataset(cfg)
            csv, meta_path = write_dataset(df, meta, Path(cfg["paths"]["processed_dir"]), "fixture")
            shas.append(hashlib.sha256(csv.read_bytes()).hexdigest())
        self.assertEqual(shas[0], shas[1])
        df = load_dataset(cfg)
        self.assertEqual(int((df.series_id == "onion_maharashtra").sum()), 731 - 3)
        self.assertEqual(int((df.series_id == "potato_uttar_pradesh").sum()), 731)

        # Forecasting runner end to end, then independent recomputation of the reported MAE
        Runner(cfg).run()
        metrics = pd.read_csv(Path(cfg["paths"]["tables_dir"]) / "forecast_test_metrics.csv")
        self.assertEqual(set(metrics.model), {"naive", "seasonal_naive", "linear_regression", "decision_tree",
                                              "random_forest", "sarima", "ets"})
        for sid in ("onion_maharashtra", "potato_uttar_pradesh"):
            f = pd.read_csv(Path(cfg["paths"]["forecasts_dir"]) / f"test_{sid}.csv")
            for m in metrics[metrics.series_id == sid].model:
                mae = np.mean(np.abs(f["actual"] - f[m]))
                self.assertAlmostEqual(mae, float(metrics[(metrics.series_id == sid) & (metrics.model == m)].mae.iloc[0]))
            # Naive forecast at each origin is exactly the origin's observed value
            np.testing.assert_array_equal(f["naive"], f["y_origin"])
            self.assertTrue((pd.to_datetime(f["target_date"]) > pd.to_datetime(f["origin_date"])).all())

        # Anomaly runner end to end
        AnomalyRunner(cfg).run()
        scores = pd.read_csv(Path(cfg["paths"]["tables_dir"]) / "anomaly_scores.csv")
        self.assertEqual(len(scores), len(df))
        self.assertTrue(scores.groupby("series_id")["composite"].apply(lambda s: s.iloc[:182].isna().all()).all())

        ok, detail = verify_run_manifests(cfg)
        self.assertTrue(ok, detail)


if __name__ == "__main__":
    unittest.main()
