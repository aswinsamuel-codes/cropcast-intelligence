"""
Reproducibility tests: seed propagation, parallel determinism, run manifests and artifact integrity.
"""

import copy
import json
import random
import tempfile
import unittest
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor

from src.experiment import RunRecorder, config_hash, seed_everything, verify_run_manifests


class TestSeeds(unittest.TestCase):
    def test_seed_everything_fixes_python_and_numpy(self):
        seed_everything(7)
        a = (random.random(), np.random.rand())
        seed_everything(7)
        b = (random.random(), np.random.rand())
        self.assertEqual(a, b)

    def test_random_forest_trees_independent_of_n_jobs(self):
        # The fitted trees are bit-identical for any n_jobs. The ensemble mean can differ in the
        # last ulp (~1e-16) because parallel prediction accumulates tree outputs in a different order.
        rng = np.random.default_rng(0)
        X, y = rng.normal(size=(300, 6)), rng.normal(size=300)
        f1 = RandomForestRegressor(n_estimators=30, random_state=5, n_jobs=1).fit(X, y)
        f4 = RandomForestRegressor(n_estimators=30, random_state=5, n_jobs=4).fit(X, y)
        for t1, t4 in zip(f1.estimators_, f4.estimators_):
            np.testing.assert_array_equal(t1.predict(X[:20]), t4.predict(X[:20]))
        np.testing.assert_allclose(f1.predict(X[:20]), f4.predict(X[:20]), rtol=1e-12, atol=1e-12)

    def test_parallel_fit_serial_predict_is_bit_identical(self):
        # Parallel *prediction* accumulates tree outputs in thread order, which varies between runs
        # (observed ~1e-16 differences, ISS-012). Fitting in parallel and predicting serially, as
        # FeatureModel does, is bit-identical across repeated runs and across n_jobs.
        rng = np.random.default_rng(0)
        X, y = rng.normal(size=(300, 6)), rng.normal(size=300)
        preds = []
        for n_jobs in (4, 4, 1):
            f = RandomForestRegressor(n_estimators=30, random_state=5, n_jobs=n_jobs).fit(X, y)
            f.set_params(n_jobs=1)
            preds.append(f.predict(X[:50]))
        np.testing.assert_array_equal(preds[0], preds[1])
        np.testing.assert_array_equal(preds[0], preds[2])

    def test_feature_model_predicts_serially(self):
        import pandas as pd
        from src.features.build import build_features
        from src.forecasting.models import SeriesData, make_feature_model
        rng = np.random.default_rng(1)
        g = pd.DataFrame({"date": pd.date_range("2021-01-01", periods=120), "modal_price": 1000 * np.exp(np.cumsum(rng.normal(0, 0.02, 120))),
                          "arrival_qty": rng.integers(1000, 9000, 120).astype(float)})
        data = SeriesData(build_features(g))
        runs = []
        for _ in range(2):
            m = make_feature_model(data, "random_forest", {"n_estimators": 20, "max_depth": 5}, seed=3, n_jobs=4)
            m.fit(100)
            self.assertEqual(m.model.n_jobs, 1)
            runs.append([m.forecast(t) for t in range(100, 110)])
        self.assertEqual(runs[0], runs[1])


class ManifestFixture(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "processed").mkdir()
        (self.root / "processed" / "cropcast_analysis_t.meta.json").write_text(json.dumps({"csv_sha256": "a" * 64}))
        self.cfg = {"random_seed": 1, "dataset": {"version": "t"},
                    "paths": {"runs_dir": str(self.root / "runs"), "processed_dir": str(self.root / "processed"),
                              "experiment_log": str(self.root / "log.jsonl")}}
        self.out = self.root / "out.csv"

    def complete_run(self, kind="forecasting"):
        rec = RunRecorder(self.cfg, kind)
        rec.start()
        self.out.write_text("x,y\n1,2\n")
        h = config_hash("t:aaaaaaaaaaaa", 1, {"f": 1}, {"m": 2})
        rec.log_record({"config_hash": h, "dataset_version": "t:aaaaaaaaaaaa", "random_seed": 1,
                        "feature_definition": {"f": 1}, "model_params_for_hash": {"m": 2}})
        rec.complete([self.out])
        return rec


class TestRunManifests(ManifestFixture):
    def test_completed_run_verifies(self):
        self.complete_run()
        ok, detail = verify_run_manifests(self.cfg, kinds=("forecasting",))
        self.assertTrue(ok, detail)

    def test_running_or_failed_latest_run_fails(self):
        self.complete_run()
        rec = RunRecorder(self.cfg, "forecasting")
        rec.start()
        ok, detail = verify_run_manifests(self.cfg, kinds=("forecasting",))
        self.assertFalse(ok)
        self.assertIn("running", detail)
        rec.fail(RuntimeError("boom"))
        ok, detail = verify_run_manifests(self.cfg, kinds=("forecasting",))
        self.assertFalse(ok)
        self.assertIn("failed", detail)

    def test_modified_artifact_detected(self):
        self.complete_run()
        self.out.write_text("x,y\n1,3\n")
        ok, detail = verify_run_manifests(self.cfg, kinds=("forecasting",))
        self.assertFalse(ok)
        self.assertIn("checksum", detail)

    def test_missing_artifact_detected(self):
        self.complete_run()
        self.out.unlink()
        ok, detail = verify_run_manifests(self.cfg, kinds=("forecasting",))
        self.assertFalse(ok)
        self.assertIn("missing", detail)

    def test_changed_config_detected(self):
        self.complete_run()
        cfg2 = copy.deepcopy(self.cfg)
        cfg2["random_seed"] = 2
        ok, detail = verify_run_manifests(cfg2, kinds=("forecasting",))
        self.assertFalse(ok)
        self.assertIn("configuration", detail)

    def test_changed_dataset_detected(self):
        self.complete_run()
        (self.root / "processed" / "cropcast_analysis_t.meta.json").write_text(json.dumps({"csv_sha256": "b" * 64}))
        ok, detail = verify_run_manifests(self.cfg, kinds=("forecasting",))
        self.assertFalse(ok)
        self.assertIn("dataset", detail)

    def test_tampered_log_hash_detected(self):
        self.complete_run()
        log = Path(self.cfg["paths"]["experiment_log"])
        rec = json.loads(log.read_text().splitlines()[0])
        rec["model_params_for_hash"] = {"m": 3}
        log.write_text(json.dumps(rec) + "\n")
        ok, detail = verify_run_manifests(self.cfg, kinds=("forecasting",))
        self.assertFalse(ok)
        self.assertIn("hash", detail)

    def test_interrupted_run_is_marked_and_never_trusted(self):
        from src.run_records import mark_interrupted
        rec = RunRecorder(self.cfg, "forecasting")
        rec.start()
        path = Path(self.cfg["paths"]["runs_dir"]) / rec.run_id / "manifest.json"
        m = mark_interrupted(path, ["process gone"])
        self.assertEqual(m["status"], "interrupted")
        self.assertEqual(m["interruption_evidence"], ["process gone"])
        ok, detail = verify_run_manifests(self.cfg, kinds=("forecasting",))
        self.assertFalse(ok)
        self.assertIn("interrupted", detail)
        with self.assertRaises(ValueError):
            mark_interrupted(path, ["again"])  # only a running manifest can be marked
        # A later completed run supersedes the interrupted one
        self.complete_run()
        ok, detail = verify_run_manifests(self.cfg, kinds=("forecasting",))
        self.assertTrue(ok, detail)

    def test_no_runs_fails(self):
        ok, detail = verify_run_manifests(self.cfg, kinds=("forecasting",))
        self.assertFalse(ok)

    def test_manifest_contents(self):
        rec = self.complete_run()
        m = json.loads((Path(self.cfg["paths"]["runs_dir"]) / rec.run_id / "manifest.json").read_text())
        for key in ("run_id", "kind", "status", "started_at", "ended_at", "git", "config_sha256", "config",
                    "dataset_version", "dataset_csv_sha256", "software", "random_seed", "artifacts"):
            self.assertIn(key, m)
        self.assertEqual(m["status"], "completed")
        self.assertIn("commit", m["git"])
        self.assertIn("dirty", m["git"])


class TestCodeProvenance(ManifestFixture):
    """Point the code fingerprint at a temporary tree so a change during a run can be simulated."""

    def setUp(self):
        super().setUp()
        import src.run_records as rr
        self.rr = rr
        self.saved = (rr.REPO_ROOT, rr.CODE_PATHS)
        self.code = self.root / "fake_repo"
        (self.code / "src").mkdir(parents=True)
        (self.code / "src" / "m.py").write_text("x = 1\n")
        rr.REPO_ROOT, rr.CODE_PATHS = self.code, ("src",)

    def tearDown(self):
        self.rr.REPO_ROOT, self.rr.CODE_PATHS = self.saved

    def test_fingerprint_identifies_code(self):
        a = self.rr.code_fingerprint()
        (self.code / "src" / "m.py").write_text("x = 2\n")
        b = self.rr.code_fingerprint()
        self.assertNotEqual(a["sha256"], b["sha256"])
        self.assertEqual(a["files"], 1)

    def test_change_during_run_is_recorded_not_hidden(self):
        rec = RunRecorder(self.cfg, "forecasting")
        rec.start()
        (self.code / "src" / "m.py").write_text("x = 2\n")
        self.out.write_text("a\n")
        rec.complete([self.out])
        m = json.loads((Path(self.cfg["paths"]["runs_dir"]) / rec.run_id / "manifest.json").read_text())
        self.assertTrue(m["tree_changed_during_run"])
        self.assertEqual(m["files_changed_during_run"], ["src/m.py"])
        self.assertNotEqual(m["code_fingerprint_start"]["sha256"], m["code_fingerprint_end"]["sha256"])
        ok, detail = verify_run_manifests(self.cfg, kinds=("forecasting",))
        self.assertTrue(ok, detail)
        self.assertIn("WARNING code changed during the run", detail)

    def test_unchanged_run_records_no_change(self):
        rec = RunRecorder(self.cfg, "forecasting")
        rec.start()
        self.out.write_text("a\n")
        rec.complete([self.out])
        m = json.loads((Path(self.cfg["paths"]["runs_dir"]) / rec.run_id / "manifest.json").read_text())
        self.assertFalse(m["tree_changed_during_run"])
        self.assertEqual(m["files_changed_during_run"], [])

    def test_retrospective_manifest_is_flagged(self):
        from src.run_records import write_retrospective_manifest
        self.out.write_text("legacy\n")
        path = write_retrospective_manifest(self.cfg, "forecasting", "2026-10-23T18:06:44+00:00",
                                            "2026-10-23T19:00:00+00:00", [self.out], ["code was uncommitted"],
                                            ("2026-10-23T18:06:44+00:00", "2026-10-23T19:00:00+00:00"))
        m = json.loads(path.read_text())
        self.assertTrue(m["retrospective"])
        self.assertIsNone(m["config_sha256"])
        self.assertEqual(m["git"]["commit"], "unknown at run time")
        ok, detail = verify_run_manifests(self.cfg, kinds=("forecasting",))
        self.assertTrue(ok, detail)
        self.assertIn("RETROSPECTIVE", detail)


if __name__ == "__main__":
    unittest.main()
