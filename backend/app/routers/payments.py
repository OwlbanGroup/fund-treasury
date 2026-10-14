"""Payment endpoints: create a pending payment, then dispatch it via the bank."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..clients import BankClient, get_bank_client
from ..database import get_db
from ..models.bank_account import BankAccount
from ..models.payment import Payment
from ..schemas import PaymentCreate, PaymentOut, PaymentSendResponse

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=list[PaymentOut])
def list_payments(
    account_id: int | None = None, db: Session = Depends(get_db)
) -> list[Payment]:
    stmt = select(Payment)
    if account_id is not None:
        stmt = stmt.where(Payment.account_id == account_id)
    return list(db.scalars(stmt.order_by(Payment.id.desc())))


@router.post("", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate, db: Session = Depends(get_db)
) -> Payment:
    account = db.get(BankAccount, payload.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    duplicate = db.scalar(
        select(Payment).where(Payment.reference == payload.reference)
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payment reference '{payload.reference}' already exists",
        )
    payment = Payment(
        account_id=account.id,
        amount=payload.amount,
        counterparty=payload.counterparty,
        reference=payload.reference,
        payment_method=payload.payment_method,
        currency=payload.currency or account.currency,
        note=payload.note,
        status="pending",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: int, db: Session = Depends(get_db)) -> Payment:
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/{payment_id}/send", response_model=PaymentSendResponse)
def send_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    bank: BankClient = Depends(get_bank_client),
) -> PaymentSendResponse:
    """Dispatch a pending payment through the bank client.

    Mock mode writes a file to the outbox; real mode calls the transport stub.
    """
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payment already '{payment.status}'",
        )

    result = bank.send_payment(payment)
    payment.status = result.status
    payment.bank_reference = result.bank_reference
    payment.outbox_file = result.outbox_file
    payment.sent_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(payment)
    return PaymentSendResponse(
        payment=PaymentOut.model_validate(payment),
        bank_reference=result.bank_reference,
        outbox_file=result.outbox_file,
    )
