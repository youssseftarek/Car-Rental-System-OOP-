models/customer.py

from __future__ import annotations
from datetime import date
from typing import Any


class Customer:
   

    MIN_PHONE_DIGITS: int = 10
    MAX_PHONE_DIGITS: int = 15

    def __init__(
        self,
        customer_id: str,
        name: str,
        phone: str,
        license_no: str,
        license_expiry: date,
    ) -> None:
        self._customer_id: str = self._require_text(customer_id, "رقم العميل")
        self._name: str = self._require_text(name, "اسم العميل")
        self._phone: str = self._validate_phone(phone)
        self._license_no: str = self._require_text(license_no, "رقم الرخصة").upper()
        self._license_expiry: date = self._validate_date(license_expiry)

            # ---------- (Validation) ----------
    @staticmethod
    def _require_text(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} مطلوب ولا يمكن أن يكون فارغاً")
        return value.strip()

    @classmethod
    def _validate_phone(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("رقم الهاتف مطلوب ولا يمكن أن يكون فارغاً")
        cleaned = value.strip().replace(" ", "").replace("-", "")
        if not cleaned.isdigit():
            raise ValueError("رقم الهاتف يجب أن يحتوي على أرقام فقط")
        if not cls.MIN_PHONE_DIGITS <= len(cleaned) <= cls.MAX_PHONE_DIGITS:
            raise ValueError(
                f"رقم الهاتف يجب أن يكون بين {cls.MIN_PHONE_DIGITS} "
                f"و {cls.MAX_PHONE_DIGITS} رقماً"
            )
        return cleaned

    @staticmethod
    def _validate_date(value: date) -> date:
        if not isinstance(value, date):
            raise ValueError("تاريخ انتهاء الرخصة غير صالح")
        return value

    # ---------- Properties (Encapsulation) ---------
    @property
    def customer_id(self) -> str:
        return self._customer_id  

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = self._require_text(value, "اسم العميل")

    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value: str) -> None:
        self._phone = self._validate_phone(value)

    @property
    def license_no(self) -> str:
        return self._license_no

    @license_no.setter
    def license_no(self, value: str) -> None:
        self._license_no = self._require_text(value, "رقم الرخصة").upper()

    @property
    def license_expiry(self) -> date:
        return self._license_expiry

    @license_expiry.setter
    def license_expiry(self, value: date) -> None:
        self._license_expiry = self._validate_date(value)

    # ---------- (Business Rule) ----------
    def is_license_valid(self, on_date: date) -> bool:
        
        return self._license_expiry >= on_date

    # ---------- JSON ----------
    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_id": self._customer_id,
            "name": self._name,
            "phone": self._phone,
            "license_no": self._license_no,
            "license_expiry": self._license_expiry.isoformat(),  # "2027-03-15"
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Customer:
        try:
            expiry = date.fromisoformat(data["license_expiry"])
            return Customer(
                customer_id=data["customer_id"],
                name=data["name"],
                phone=data["phone"],
                license_no=data["license_no"],
                license_expiry=expiry,
            )
        except KeyError as e:
            raise ValueError(f"بيانات العميل ناقصة: {e}") from e
        except (TypeError, ValueError) as e:
            raise ValueError(f"بيانات العميل غير صالحة: {e}") from e

    def __str__(self) -> str:
        return f"{self._name} ({self._customer_id})"