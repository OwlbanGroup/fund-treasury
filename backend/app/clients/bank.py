"""Bank connectivity client.

``BANK_MODE`` controls behaviour:

* ``mock`` (default) — generates a payment file into ``BANK_FILE_OUTBOX`` and
  returns a synthetic acknowledgement. Fully offline.
* ``real`` — a documented stub that would call the bank's file-transfer API.
  It intentionally raises if used without wiring in real credentials so that
  no silent, half-configured submission ever happens in production.
"""
from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from ..config import get_settings
from ..models.payment import Payment
from .bank_types import SendResult

logger = logging.getLogger(__name__)


class BankError(RuntimeError):
    """Raised when a real bank submission is attempted but not configured."""


class BankClient:
    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def is_mock(self) -> bool:
        return self._settings.BANK_MODE.lower() != "real"

    def send_payment(self, payment: Payment) -> SendResult:
        """Dispatch a payment.

        In mock mode this writes a simple pipe-delimited instruction file to the
        outbox directory and returns ``status='sent'`` with a bank reference.
        """
        if self.is_mock:
            return self._mock_send(payment)
        return self._real_send(payment)

    # --- Mock -------------------------------------------------------------
    def _mock_send(self, payment: Payment) -> SendResult:
        outbox = Path(self._settings.BANK_FILE_OUTBOX)
        outbox.mkdir(parents=True, exist_ok=True)
        filename = f"payment_{payment.id}_{uuid4().hex[:8]}.txt"
        path = outbox / filename
        content = (
            "PAYMENT|"
            f"{payment.reference}|"
            f"{payment.currency}|"
            f"{payment.amount}|"
            f"{payment.counterparty}|"
            f"{payment.payment_method}|"
            f"{payment.account.account_number_masked}"
        )
        path.write_text(content, encoding="utf-8")
        logger.info("Mock bank wrote payment file: %s", path)
        return SendResult(
            status="sent",
            bank_reference=f"MOCK-{uuid4().hex[:12].upper()}",
            outbox_file=str(path),
        )

    # --- Real (stub) ------------------------------------------------------
    def _real_send(self, payment: Payment) -> SendResult:
        # Real SFTP/H2H integration is environment-specific. Raise loudly rather
        # than pretending success. Implement against your bank's transport here.
        raise BankError(
            "BANK_MODE=real requires a bank transport implementation. "
            "Wire up SFTP/H2H in BankClient._real_send before enabling it."
        )


def get_bank_client() -> BankClient:
    """FastAPI dependency factory."""
    return BankClient()
