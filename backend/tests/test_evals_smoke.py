"""Smoke test: eval harness runner stays import-safe under pytest."""
from __future__ import annotations

import importlib


def test_eval_module_imports():
    ev = importlib.import_module("evals.run_evals")
    assert hasattr(ev, "main")
    assert hasattr(ev, "EvalResult")
    assert hasattr(ev, "eval_forecast_math")
    assert hasattr(ev, "eval_payment_lifecycle")
