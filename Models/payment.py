

from __future__ import annotations

from datetime import date
from typing import Any


class Payment:

    CASH: str = "cash"
    CARD: str = "card"
    TRANSFER: str = "transfer"
    VALID_METHODS: tuple[str, ...] = (CASH, CARD, TRANSFER)

    def __init__(
        self,
        payment_id: str,
        rental_id: str,
        amount: float,
        payment_date: date,
        method: str,
    ) -> None:
        self._payment_id: str = self._require_text(payment_id, "رقم الدفعة")
        self._rental_id: str = self._require_text(rental_id, "رقم الإيجار")
        self._amount: float = self._validate_amount(amount)
        self._payment_date: date = self._validate_date(payment_date)
        self._method: str = self._validate_method(method)

    # ---------- (Validation) ----------
    @staticmethod
    def _require_text(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} مطلوب ولا يمكن أن يكون فارغاً")
        return value.strip()

    @staticmethod
    def _validate_amount(value: float) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("المبلغ يجب أن يكون رقماً")
        if value <= 0:
            raise ValueError("المبلغ يجب أن يكون أكبر من صفر") 
        return round(float(value), 2)

    @staticmethod
    def _validate_date(value: date) -> date:
        if not isinstance(value, date):
            raise ValueError("تاريخ الدفع غير صالح")
        return value

    @classmethod
    def _validate_method(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("طريقة الدفع غير صالحة")
        method = value.strip().lower()
        if method not in cls.VALID_METHODS:
            allowed = " / ".join(cls.VALID_METHODS)
            raise ValueError(f"طريقة الدفع غير صالحة، المسموح: {allowed}")
        return method

    # ---------- Properties (Encapsulation) ----------
    @property
    def payment_id(self) -> str:
        return self._payment_id

    @property
    def rental_id(self) -> str:
        return self._rental_id

    @property
    def amount(self) -> float:
        return self._amount

    @amount.setter
    def amount(self, value: float) -> None:
        self._amount = self._validate_amount(value)

    @property
    def payment_date(self) -> date:
        return self._payment_date

    @property
    def method(self) -> str:
        return self._method

    @method.setter
    def method(self, value: str) -> None:
        self._method = self._validate_method(value)

    # ---------- JSON ----------
    def to_dict(self) -> dict[str, Any]:
        return {
            "payment_id": self._payment_id,
            "rental_id": self._rental_id,
            "amount": self._amount,
            "payment_date": self._payment_date.isoformat(),
            "method": self._method,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Payment:
        try:
            return Payment(
                payment_id=data["payment_id"],
                rental_id=data["rental_id"],
                amount=data["amount"],
                payment_date=date.fromisoformat(data["payment_date"]),
                method=data["method"],
            )
        except KeyError as e:
            raise ValueError(f"بيانات الدفعة ناقصة: {e}") from e
        except (TypeError, ValueError) as e:
            raise ValueError(f"بيانات الدفعة غير صالحة: {e}") from e

    def __str__(self) -> str:
        return f"{self._payment_id}: {self._amount:.2f} EGP ({self._method})"