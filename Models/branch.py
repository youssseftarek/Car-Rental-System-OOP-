
from __future__ import annotations

from typing import Any


class Branch:

    def __init__(self, branch_id: str, name: str, address: str) -> None:
        self._branch_id: str = self._require_text(branch_id, "رقم الفرع")
        self._name: str = self._require_text(name, "اسم الفرع")
        self._address: str = self._require_text(address, "عنوان الفرع")
        
    # ---------- (Validation) ----------
    @staticmethod
    def _require_text(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} مطلوب ولا يمكن أن يكون فارغاً")
        return value.strip()

    # ---------- Properties ----------
    @property
    def branch_id(self) -> str:
        return self._branch_id 

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = self._require_text(value, "اسم الفرع")

    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, value: str) -> None:
        self._address = self._require_text(value, "عنوان الفرع")

    # --------- JSON ----------
    def to_dict(self) -> dict[str, Any]:
        return {
            "branch_id": self._branch_id,
            "name": self._name,
            "address": self._address,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Branch:
        try:
            return Branch(
                branch_id=data["branch_id"],
                name=data["name"],
                address=data["address"],
            )
        except KeyError as e:
            raise ValueError(f"بيانات الفرع ناقصة: {e}") from e

    def __str__(self) -> str:
        return f"{self._name} ({self._branch_id})"