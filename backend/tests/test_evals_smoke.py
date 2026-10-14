"""Smoke test: eval harness runner stays import-safe under pytest."""
from __future__ import annotations

import evals.run_evals as ev


def test_eval_module_imports():
    assert hasattr(ev, "main")
    assert hasattr(ev, "EvalResult")
    assert hasattr(ev, "eval_forecast_math")
    assert hasattr(ev, "eval_payment_lifecycle")
