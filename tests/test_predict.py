"""Tests for the final pipeline artifact and src.predict.

    python -m unittest discover -s tests -v      (from the project root)

Requires models/final_pipeline.joblib (python scripts/train_final.py). Uses training rows only.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import (ALERT_TAU, FAMILIES, MODELS_DIR, USE_CLASS_WEIGHT,
                        USE_ENGINEERED)
from src.data import load_train
from src.features import add_features
from src.predict import (REQUIRED_COLS, SchemaError, load_model, predict_batch,
                         predict_connection)


class FinalPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_model()  # fails loudly if the artifact is missing
        X, y, _ = load_train()
        # one row of every family plus a random slice, all from TRAIN
        idx = [int(np.flatnonzero(y.values == f)[0]) for f in FAMILIES]
        idx += list(np.random.default_rng(0).choice(len(X), 200, replace=False))
        cls.X = X.iloc[idx].reset_index(drop=True)
        cls.y = y.iloc[idx].reset_index(drop=True)
        cls.record = cls.X.iloc[FAMILIES.index("R2L")].to_dict()

    # -- artifact ------------------------------------------------------------
    def test_artifact_matches_frozen_config(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from train_final import build_final_pipeline
        pipe, winner, choice, _ = build_final_pipeline()
        decision = json.loads((MODELS_DIR / "selection_decision.json").read_text())
        self.assertEqual(winner, decision["winner"])
        self.assertEqual(choice, decision["chosen_config"][winner])
        self.assertEqual(pipe.get_params()["clf"].get_params(),
                         self.model.named_steps["clf"].get_params())
        self.assertEqual("features" in self.model.named_steps, USE_ENGINEERED)
        self.assertEqual(self.model.named_steps["clf"].class_weight is not None, USE_CLASS_WEIGHT)

    def test_save_load_roundtrip_preserves_predictions(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.joblib"
            joblib.dump(self.model, path)
            reloaded = joblib.load(path)
        np.testing.assert_array_equal(self.model.predict_proba(self.X[REQUIRED_COLS]),
                                      reloaded.predict_proba(self.X[REQUIRED_COLS]))

    # -- single / batch --------------------------------------------------------
    def test_single_and_batch_agree(self):
        batch = predict_batch(self.X)
        self.assertEqual(len(batch), len(self.X))
        single = predict_connection(self.X.iloc[3].to_dict())
        for k in ["alert", "predicted_family", "attack_score", "probabilities"]:
            self.assertEqual(single[k], batch[3][k])

    def test_output_is_json_serializable(self):
        out = predict_batch(self.X)
        self.assertEqual(json.loads(json.dumps(out)), out)
        self.assertEqual(set(out[0]), {"alert", "predicted_family", "attack_score", "threshold",
                                       "probabilities", "unseen_categories", "timestamp"})
        self.assertEqual(out[0]["threshold"], ALERT_TAU)

    def test_deterministic(self):
        strip = lambda rows: [{k: v for k, v in r.items() if k != "timestamp"} for r in rows]
        self.assertEqual(strip(predict_batch(self.X)), strip(predict_batch(self.X)))

    def test_column_order_and_extra_fields_ignored(self):
        shuffled = self.X[REQUIRED_COLS[::-1]].assign(num_outbound_cmds=0, is_host_login=0, label="x")
        a = predict_batch(self.X)
        b = predict_batch(shuffled)
        self.assertEqual([r["probabilities"] for r in a], [r["probabilities"] for r in b])

    # -- probabilities and decision rule ----------------------------------------
    def test_probability_columns_map_to_labels(self):
        raw = self.model.predict_proba(self.X[REQUIRED_COLS])
        classes = list(self.model.named_steps["clf"].classes_)
        out = predict_batch(self.X)
        for i, r in enumerate(out):
            for f in FAMILIES:
                self.assertEqual(r["probabilities"][f], raw[i, classes.index(f)])
            self.assertAlmostEqual(r["attack_score"], 1.0 - r["probabilities"]["Normal"])
        # the model's own argmax agrees with the reordered columns
        argmax = [max(r["probabilities"], key=r["probabilities"].get) for r in out]
        self.assertEqual(argmax, list(self.model.predict(self.X[REQUIRED_COLS])))

    def test_threshold_below_at_above(self):
        s = predict_connection(self.record)["attack_score"]
        self.assertGreater(s, 0.0)
        above = predict_connection(self.record, tau=np.nextafter(s, 2.0))   # score < tau
        at = predict_connection(self.record, tau=s)                          # score == tau
        below = predict_connection(self.record, tau=np.nextafter(s, -1.0))  # score > tau
        self.assertFalse(above["alert"]); self.assertEqual(above["predicted_family"], "Normal")
        self.assertTrue(at["alert"]); self.assertTrue(below["alert"])
        attacks = {f: p for f, p in at["probabilities"].items() if f != "Normal"}
        self.assertEqual(at["predicted_family"], max(attacks, key=attacks.get))

    def test_alert_flag_consistent_with_frozen_tau(self):
        for r in predict_batch(self.X):
            self.assertEqual(r["alert"], r["attack_score"] >= ALERT_TAU)
            self.assertEqual(r["alert"], r["predicted_family"] != "Normal")

    # -- preprocessing consistency ------------------------------------------------
    def test_engineered_features_match_training_definition(self):
        X = self.X[REQUIRED_COLS]
        pd.testing.assert_frame_equal(self.model.named_steps["features"].transform(X), add_features(X))

    def test_categorical_one_hot(self):
        pre = self.model.named_steps["pre"]
        names = list(pre.get_feature_names_out())
        Xt = pre.transform(self.model.named_steps["features"].transform(self.X[REQUIRED_COLS].iloc[:1]))
        self.assertEqual(Xt.shape[1], len(names))
        svc = self.X.iloc[0]["service"]
        self.assertEqual(Xt[0, names.index(f"cat__service_{svc}")], 1.0)

    def test_unseen_category_is_reported_not_rejected(self):
        out = predict_connection({**self.record, "service": "not_a_service"})
        self.assertEqual(out["unseen_categories"], {"service": "not_a_service"})
        self.assertEqual(predict_connection(self.record)["unseen_categories"], {})

    # -- schema errors -------------------------------------------------------------
    def test_schema_errors(self):
        bad = {
            "missing field": {k: v for k, v in self.record.items() if k != "src_bytes"},
            "non-numeric": {**self.record, "src_bytes": "abc"},
            "negative": {**self.record, "duration": -1},
            "nan": {**self.record, "count": float("nan")},
            "inf": {**self.record, "count": float("inf")},
            "categorical not str": {**self.record, "protocol_type": 6},
        }
        for case, rec in bad.items():
            with self.subTest(case=case), self.assertRaises(SchemaError):
                predict_connection(rec)
        with self.assertRaises(SchemaError):
            predict_connection([self.record])
        with self.assertRaises(SchemaError):
            predict_batch(self.X.iloc[:0])

    # -- documented entry point -------------------------------------------------------
    def test_cli(self):
        rec = {k: (v.item() if hasattr(v, "item") else v) for k, v in self.record.items()}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump([rec, rec], f)
        res = subprocess.run([sys.executable, "-m", "src.predict", f.name],
                             cwd=ROOT, capture_output=True, text=True, timeout=120)
        Path(f.name).unlink()
        self.assertEqual(res.returncode, 0, res.stderr)
        out = json.loads(res.stdout)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["probabilities"], predict_connection(self.record)["probabilities"])


if __name__ == "__main__":
    unittest.main()
