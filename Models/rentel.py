
from __future__ import annotations

from datetime import date
from typing import Any, Mapping

from Models.customer import Customer
from Models.payment import Payment
from Models.vehicle import Vehicle


class Rental:

    ACTIVE: str = "active"
    RETURNED: str = "returned"
    VALID_STATUSES: tuple[str, ...] = (ACTIVE, RETURNED)

    LATE_FEE_MULTIPLIER: float = 1.5  

    def __init__(
        self,
        rental_id: str,
        vehicle: Vehicle,
        customer: Customer,
        start_date: date,
        end_date: date,
        returned_on: date | None = None,
        status: str = "active",
        payments: list[Payment] | None = None,
    ) -> None:
        self._rental_id: str = self._require_text(rental_id, "رقم الإيجار")

        if not isinstance(vehicle, Vehicle):
            raise ValueError("السيارة غير صالحة")
        if not isinstance(customer, Customer):
            raise ValueError("العميل غير صالح")
        self._vehicle: Vehicle = vehicle
        self._customer: Customer = customer

        if not isinstance(start_date, date) or not isinstance(end_date, date):
            raise ValueError("تاريخ الاستلام أو الإرجاع غير صالح")
        if end_date < start_date:
            raise ValueError("تاريخ الإرجاع لا يمكن أن يكون قبل تاريخ الاستلام")
        self._start_date: date = start_date
        self._end_date: date = end_date

        if status not in self.VALID_STATUSES:
            raise ValueError(f"حالة الإيجار غير صالحة: {status}")
        if status == self.RETURNED and returned_on is None:
            raise ValueError("الإيجار المُرجَع لازم يكون له تاريخ إرجاع فعلي")
        if status == self.ACTIVE and returned_on is not None:
            raise ValueError("الإيجار النشط لا يمكن أن يكون له تاريخ إرجاع فعلي")
        if returned_on is not None and returned_on < start_date:
            raise ValueError("تاريخ الإرجاع الفعلي قبل تاريخ الاستلام")
        self._returned_on: date | None = returned_on
        self._status: str = status

        self._payments: list[Payment] = []
        for payment in payments or []:
            if payment.rental_id != self._rental_id:
                raise ValueError(f"الدفعة {payment.payment_id} تخص إيجاراً آخر")
            self._payments.append(payment)

    # ---------- (Validation) ----------
    @staticmethod
    def _require_text(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} مطلوب ولا يمكن أن يكون فارغاً")
        return value.strip()

    # ---------- Properties ----------
    @property
    def rental_id(self) -> str:
        return self._rental_id

    @property
    def vehicle(self) -> Vehicle:
        return self._vehicle

    @property
    def customer(self) -> Customer:
        return self._customer

    @property
    def start_date(self) -> date:
        return self._start_date

    @property
    def end_date(self) -> date:
        return self._end_date

    @property
    def returned_on(self) -> date | None:
        return self._returned_on

    @property
    def status(self) -> str:
        return self._status

    @property
    def payments(self) -> list[Payment]:
        return list(self._payments)  

    @property
    def days(self) -> int:
        return max(1, (self._end_date - self._start_date).days)

    # ---------- (Business Logic) ----------
    def calculate_cost(self) -> float:

        per_day = (
            self._vehicle.calculate_daily_rate()
            + self._vehicle.calculate_insurance()
        )
        return round(self.days * per_day, 2)

    def calculate_late_fee(self, return_date: date | None = None) -> float:

        reference = return_date or self._returned_on
        if reference is None or reference <= self._end_date:
            return 0.0
        late_days = (reference - self._end_date).days
        daily = self._vehicle.calculate_daily_rate()
        return round(late_days * daily * self.LATE_FEE_MULTIPLIER, 2)

    def total_due(self) -> float:
        return round(self.calculate_cost() + self.calculate_late_fee(), 2)

    def total_paid(self) -> float:
        return round(sum(p.amount for p in self._payments), 2)

    def remaining(self) -> float:
        return round(max(0.0, self.total_due() - self.total_paid()), 2)

    def is_fully_paid(self) -> bool:
        return self.remaining() == 0

    def is_active(self) -> bool:
        return self._status == self.ACTIVE

    def is_overdue(self, today: date) -> bool:
        return self.is_active() and today > self._end_date

    # ----------( Payment ) ----------
    def add_payment(self, payment: Payment) -> None:
        if payment.rental_id != self._rental_id:
            raise ValueError("هذه الدفعة تخص إيجاراً آخر")
        if payment.amount > self.remaining():
            raise ValueError(
                f"المبلغ ({payment.amount:.2f}) أكبر من المتبقي "
                f"({self.remaining():.2f})"
            )
        self._payments.append(payment)

    # ---------- قفل الإيجار ----------
    def close(self, return_date: date) -> None:
        if not isinstance(return_date, date):
            raise ValueError("تاريخ الإرجاع غير صالح")
        if self._status == self.RETURNED:
            raise ValueError("هذا الإيجار تم إرجاعه بالفعل")
        if return_date < self._start_date:
            raise ValueError("تاريخ الإرجاع لا يمكن أن يكون قبل تاريخ الاستلام")

        self._vehicle.mark_available()  
        self._returned_on = return_date
        self._status = self.RETURNED

    # ---------- JSON ----------
    def to_dict(self) -> dict[str, Any]:

        return {
            "rental_id": self._rental_id,
            "vehicle_plate": self._vehicle.plate,
            "customer_id": self._customer.customer_id,
            "start_date": self._start_date.isoformat(),
            "end_date": self._end_date.isoformat(),
            "returned_on": self._returned_on.isoformat() if self._returned_on else None,
            "status": self._status,
            "payments": [p.to_dict() for p in self._payments],
        }

    @staticmethod
    def from_dict(
        data: dict[str, Any],
        vehicles: Mapping[str, Vehicle],
        customers: Mapping[str, Customer],
    ) -> Rental:
        
        try:
            plate = data["vehicle_plate"]
            customer_id = data["customer_id"]
            if plate not in vehicles:
                raise ValueError(f"السيارة {plate} غير موجودة")
            if customer_id not in customers:
                raise ValueError(f"العميل {customer_id} غير موجود")
            returned = data.get("returned_on")
            return Rental(
                rental_id=data["rental_id"],
                vehicle=vehicles[plate],
                customer=customers[customer_id],
                start_date=date.fromisoformat(data["start_date"]),
                end_date=date.fromisoformat(data["end_date"]),
                returned_on=date.fromisoformat(returned) if returned else None,
                status=data["status"],
                payments=[Payment.from_dict(p) for p in data.get("payments", [])],
            )
        except KeyError as e:
            raise ValueError(f"بيانات الإيجار ناقصة: {e}") from e
        except TypeError as e:
            raise ValueError(f"بيانات الإيجار غير صالحة: {e}") from e

    def __str__(self) -> str:
        return (
            f"{self._rental_id}: {self._customer.name} - "
            f"{self._vehicle.plate} ({self._status})"
        )