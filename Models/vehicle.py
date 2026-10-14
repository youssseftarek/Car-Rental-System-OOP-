
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

# ---------- (Abstract Class) ----------
class Vehicle(ABC):

    # CARS TYPE 
    AVAILABLE: str = "available"
    RENTED: str = "rented"
    MAINTENANCE: str = "maintenance"
    VALID_STATUSES: tuple[str, ...] = (AVAILABLE, RENTED, MAINTENANCE)

    def __init__(
        self,
        plate: str,
        brand: str,
        model: str,
        base_rate: float,
        branch_id: str,
        status: str = "available",
    ) -> None:
        
        self._plate: str = self._require_text(plate, "رقم اللوحة").upper()
        self._brand: str = self._require_text(brand, "الماركة")
        self._model: str = self._require_text(model, "الموديل")
        self._base_rate: float = self._validate_rate(base_rate)
        self._branch_id: str = self._require_text(branch_id, "الفرع")
        if status not in self.VALID_STATUSES:
            raise ValueError(f"حاله غير صالحة: {status}")
        self._status: str = status

    # ----------  (Validation) ----------

    @staticmethod
    def _require_text(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} مطلوب ولا يمكن أن يكون فارغاً")
        return value.strip()

    @staticmethod
    def _validate_rate(value: float) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("السعر يجب أن يكون رقماً")
        if value <= 0:
            raise ValueError("السعر يجب أن يكون أكبر من صفر")
        return float(value)

    # ---------- Properties (Encapsulation) ----------

    @property
    def plate(self) -> str:
        return self._plate  

    @property
    def brand(self) -> str:
        return self._brand

    @property
    def model(self) -> str:
        return self._model

    @property
    def base_rate(self) -> float:
        return self._base_rate

    @base_rate.setter
    def base_rate(self, value: float) -> None:
        self._base_rate = self._validate_rate(value)

    @property
    def branch_id(self) -> str:
        return self._branch_id

    @branch_id.setter
    def branch_id(self, value: str) -> None:
        self._branch_id = self._require_text(value, "الفرع")

    @property
    def status(self) -> str:
        return self._status  

    @property
    def type_name(self) -> str:
        return type(self).__name__  # EconomyCar / SUV / LuxuryCar

    # ---------- (Abstract methods) ----------

    @abstractmethod
    def calculate_daily_rate(self) -> float:
        """السعر اليومي حسب نوع السيارة."""

    @abstractmethod
    def calculate_insurance(self) -> float:
        """التأمين حسب نوع السيارة."""

    # _____________________   (Business Rules)  ______________________

    def is_available(self) -> bool:
        return self._status == self.AVAILABLE

    def mark_rented(self) -> None:
        if self._status == self.RENTED:
            raise ValueError(f"السيارة {self._plate} مؤجرة بالفعل")
        if self._status == self.MAINTENANCE:
            raise ValueError(f"السيارة {self._plate} تحت الصيانة")
        self._status = self.RENTED

    def mark_available(self) -> None:
        if self._status == self.AVAILABLE:
            raise ValueError(f"السيارة {self._plate} متاحة بالفعل")
        self._status = self.AVAILABLE

    def send_to_maintenance(self) -> None:
        if self._status == self.RENTED:
            raise ValueError(f"السيارة {self._plate} مؤجرة ولا يمكن إرسالها للصيانة")
        self._status = self.MAINTENANCE

    # ---------- (JSON) ----------

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type_name,
            "plate": self._plate,
            "brand": self._brand,
            "model": self._model,
            "base_rate": self._base_rate,
            "branch_id": self._branch_id,
            "status": self._status,
        }
    # ______________ (JSON) ______________ 

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Vehicle:
 
        try:
            vehicle_class = VEHICLE_TYPES[data["type"]]
            return vehicle_class(
                plate=data["plate"],
                brand=data["brand"],
                model=data["model"],
                base_rate=data["base_rate"],
                branch_id=data["branch_id"],
                status=data.get("status", Vehicle.AVAILABLE),
            )
        except KeyError as e:
            raise ValueError(f"بيانات السيارة ناقصة أو نوعها غير معروف: {e}") from e

    def __str__(self) -> str:
        return f"{self._brand} {self._model} ({self._plate}) - {self._status}"


class EconomyCar(Vehicle):

    RATE_MULTIPLIER: float = 1.0
    INSURANCE_RATE: float = 0.05

    def calculate_daily_rate(self) -> float:
        return round(self._base_rate * self.RATE_MULTIPLIER, 2)

    def calculate_insurance(self) -> float:
        return round(self.calculate_daily_rate() * self.INSURANCE_RATE, 2)


class SUV(Vehicle):

    RATE_MULTIPLIER: float = 1.5
    INSURANCE_RATE: float = 0.08

    def calculate_daily_rate(self) -> float:
        return round(self._base_rate * self.RATE_MULTIPLIER, 2)

    def calculate_insurance(self) -> float:
        return round(self.calculate_daily_rate() * self.INSURANCE_RATE, 2)


class LuxuryCar(Vehicle):

    RATE_MULTIPLIER: float = 2.5
    INSURANCE_RATE: float = 0.12

    def calculate_daily_rate(self) -> float:
        return round(self._base_rate * self.RATE_MULTIPLIER, 2)

    def calculate_insurance(self) -> float:
        return round(self.calculate_daily_rate() * self.INSURANCE_RATE, 2)


VEHICLE_TYPES: dict[str, type[Vehicle]] = {
    "EconomyCar": EconomyCar,
    "SUV": SUV,
    "LuxuryCar": LuxuryCar,
}