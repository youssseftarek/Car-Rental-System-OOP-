from __future__ import annotations

from datetime import date
from typing import Iterable

from File_Manger.File_manger import FileManager
from Models.branch import Branch
from Models.customer import Customer
from Models.payment import Payment
from Models.rentel import Rental
from Models.vehicle import VEHICLE_TYPES, Vehicle


class CarRental:

    BRANCHES_FILE: str = "branches.json"
    VEHICLES_FILE: str = "vehicles.json"
    CUSTOMERS_FILE: str = "customers.json"
    RENTALS_FILE: str = "rentals.json"

    def __init__(self, file_manager: FileManager, autosave: bool = True) -> None:
        # Composition: 
        self._branches: list[Branch] = []
        self._vehicles: list[Vehicle] = []
        self._customers: list[Customer] = []
        self._rentals: list[Rental] = []
        # Dependency: 
        self._fm: FileManager = file_manager
        self._autosave: bool = autosave

    # ------------------------------------------------------------------
    # قراءة القوائم (نسخ، عشان محدش يعدّل القوائم الأصلية من بره)
    # ------------------------------------------------------------------
    @property
    def branches(self) -> list[Branch]:
        return list(self._branches)

    @property
    def vehicles(self) -> list[Vehicle]:
        return list(self._vehicles)

    @property
    def customers(self) -> list[Customer]:
        return list(self._customers)

    @property
    def rentals(self) -> list[Rental]:
        return list(self._rentals)


    # ---------- (Validation) ----------
    @staticmethod
    def _next_id(prefix: str, existing: Iterable[str], width: int = 3) -> str:
        # C001 ثم C002 : يولّد الرقم التالي
        numbers = [
            int(i[len(prefix):])
            for i in existing
            if i.startswith(prefix) and i[len(prefix):].isdigit()
        ]
        return f"{prefix}{max(numbers, default=0) + 1:0{width}d}"

    @staticmethod
    def _today(today: date | None) -> date:
        return today or date.today()

    def _changed(self) -> None:
        if self._autosave:
            self.save()

    # ------------------------------------------------------------------
    #  البحث عن طريق المفتاح (ID أو Plate) : بيرجع object أو يرفع ValueError لو مش موجود
    # ------------------------------------------------------------------
    def get_branch(self, branch_id: str) -> Branch:
        for branch in self._branches:
            if branch.branch_id == branch_id:
                return branch
        raise ValueError(f"الفرع {branch_id} غير موجود")

    def get_vehicle(self, plate: str) -> Vehicle:
        key = (plate or "").strip().upper()
        for vehicle in self._vehicles:
            if vehicle.plate == key:
                return vehicle
        raise ValueError(f"السيارة {plate} غير موجودة") 

    def get_customer(self, customer_id: str) -> Customer:
        for customer in self._customers:
            if customer.customer_id == customer_id:
                return customer
        raise ValueError(f"العميل {customer_id} غير موجود")

    def get_rental(self, rental_id: str) -> Rental:
        for rental in self._rentals:
            if rental.rental_id == rental_id:
                return rental
        raise ValueError(f"الإيجار {rental_id} غير موجود")


    # 1) ____________________ Branch (CRUD) __________________________

    def add_branch(self, name: str, address: str) -> Branch:
        branch_id = self._next_id("B", (b.branch_id for b in self._branches), 2)
        branch = Branch(branch_id, name, address)
        self._branches.append(branch)
        self._changed()
        return branch

    def update_branch(self, branch_id: str, name: str, address: str) -> Branch:
        branch = self.get_branch(branch_id)
        Branch(branch_id, name, address)  # تحقق من القيم الجديدة قبل ما نغيّر
        branch.name = name
        branch.address = address
        self._changed()
        return branch

    def delete_branch(self, branch_id: str) -> None:
        branch = self.get_branch(branch_id)
        if any(v.branch_id == branch_id for v in self._vehicles):
            raise ValueError("لا يمكن حذف فرع فيه سيارات")
        self._branches.remove(branch)
        self._changed()

    # 2) _____________________ vehicle (CRUD) ___________________________

    def add_vehicle(
        self,
        type_name: str,
        plate: str,
        brand: str,
        model: str,
        base_rate: float,
        branch_id: str,
    ) -> Vehicle:
        vehicle_class = VEHICLE_TYPES.get(type_name)
        if vehicle_class is None:
            allowed = " / ".join(VEHICLE_TYPES)
            raise ValueError(f"نوع السيارة غير صالح، المسموح: {allowed}")
        self.get_branch(branch_id)  

        vehicle = vehicle_class(plate, brand, model, base_rate, branch_id)
        if any(v.plate == vehicle.plate for v in self._vehicles):
            raise ValueError(f"رقم اللوحة {vehicle.plate} مسجل من قبل")
        self._vehicles.append(vehicle)
        self._changed()
        return vehicle

    def update_vehicle(
        self,
        plate: str,
        base_rate: float | None = None,
        branch_id: str | None = None,
    ) -> Vehicle:
        vehicle = self.get_vehicle(plate)
        if branch_id is not None:
            self.get_branch(branch_id) 
        if base_rate is not None:
            vehicle.base_rate = base_rate  
        if branch_id is not None:
            vehicle.branch_id = branch_id
        self._changed()
        return vehicle

    def delete_vehicle(self, plate: str) -> None:
        vehicle = self.get_vehicle(plate)
        if any(r.vehicle is vehicle for r in self._rentals):
            raise ValueError("لا يمكن حذف سيارة لها سجل إيجارات")
        self._vehicles.remove(vehicle)
        self._changed()

    def send_to_maintenance(self, plate: str) -> Vehicle:
        vehicle = self.get_vehicle(plate)
        vehicle.send_to_maintenance()
        self._changed()
        return vehicle

    def finish_maintenance(self, plate: str) -> Vehicle:
        vehicle = self.get_vehicle(plate)
        if vehicle.status != Vehicle.MAINTENANCE:
            raise ValueError("السيارة ليست تحت الصيانة")
        vehicle.mark_available()
        self._changed()
        return vehicle

    # 3) _____________________ Customer (CRUD) ___________________________
  
    def add_customer(
        self, name: str, phone: str, license_no: str, license_expiry: date
    ) -> Customer:
        customer_id = self._next_id("C", (c.customer_id for c in self._customers))
        customer = Customer(customer_id, name, phone, license_no, license_expiry)
        if any(c.license_no == customer.license_no for c in self._customers):
            raise ValueError(f"رقم الرخصة {customer.license_no} مسجل لعميل آخر")
        self._customers.append(customer)
        self._changed()
        return customer

    def update_customer(
        self,
        customer_id: str,
        name: str,
        phone: str,
        license_no: str,
        license_expiry: date,
    ) -> Customer:
        customer = self.get_customer(customer_id)
        # object مؤقت: لو أي قيمة غلط يرفع الخطأ قبل ما نغيّر أي حاجة
        checked = Customer(customer_id, name, phone, license_no, license_expiry)
        for other in self._customers:
            if other is not customer and other.license_no == checked.license_no:
                raise ValueError(f"رقم الرخصة {checked.license_no} مسجل لعميل آخر")
        customer.name = checked.name
        customer.phone = checked.phone
        customer.license_no = checked.license_no
        customer.license_expiry = checked.license_expiry
        self._changed()
        return customer

    def delete_customer(self, customer_id: str) -> None:
        customer = self.get_customer(customer_id)
        if any(r.customer is customer for r in self._rentals):
            raise ValueError("لا يمكن حذف عميل له سجل إيجارات")
        self._customers.remove(customer)
        self._changed()

    # 4) _____________________ التأجير والإرجاع والدفع (قلب الـ Business Logic) ___________________________
   
    def rent_car(
        self,
        plate: str,
        customer_id: str,
        start_date: date,
        end_date: date,
        today: date | None = None,
    ) -> Rental:
        
        today = self._today(today)

        vehicle = self.get_vehicle(plate)              #  السيارة موجودة؟
        customer = self.get_customer(customer_id)      #  العميل موجود؟

        if not isinstance(start_date, date) or not isinstance(end_date, date):
            raise ValueError("تاريخ الاستلام أو الإرجاع غير صالح")
        if start_date < today:                         #  لا إيجار بأثر رجعي
            raise ValueError("تاريخ الاستلام لا يمكن أن يكون في الماضي")
        if end_date < start_date:                      #  الإرجاع بعد الاستلام
            raise ValueError("تاريخ الإرجاع لا يمكن أن يكون قبل تاريخ الاستلام")
        if not vehicle.is_available():                 #  السيارة متاحة؟
            raise ValueError(
                f"السيارة {vehicle.plate} غير متاحة (الحالة: {vehicle.status})"
            )
        if not customer.is_license_valid(end_date):    #  الرخصة سارية لآخر يوم
            raise ValueError("رخصة العميل ستنتهي قبل نهاية فترة الإيجار")

        rental_id = self._next_id("R", (r.rental_id for r in self._rentals))
        rental = Rental(rental_id, vehicle, customer, start_date, end_date)
        vehicle.mark_rented()
        self._rentals.append(rental)
        self._changed()
        return rental

    def return_car(
        self,
        rental_id: str,
        return_date: date | None = None,
        today: date | None = None,
    ) -> Rental:
        today = self._today(today)
        return_date = return_date or today
        if return_date > today:
            raise ValueError("تاريخ الإرجاع لا يمكن أن يكون في المستقبل")
        rental = self.get_rental(rental_id)
        rental.close(return_date)  # بيرفض: قبل الاستلام، أو مرتجع قبل كده
        self._changed()
        return rental

    def record_payment(
        self,
        rental_id: str,
        amount: float,
        method: str,
        payment_date: date | None = None,
    ) -> Payment:
        rental = self.get_rental(rental_id)
        all_ids = (p.payment_id for r in self._rentals for p in r.payments)
        payment_id = self._next_id("P", all_ids)
        payment = Payment(
            payment_id, rental_id, amount, payment_date or date.today(), method
        )
        rental.add_payment(payment)  # بيرفض لو أكبر من المتبقي
        self._changed()
        return payment

    # 5) ___________________ search and filter ___________________________
    def search_vehicles(self, text: str) -> list[Vehicle]:
        key = text.strip().lower()
        return [
            v for v in self._vehicles
            if key in v.plate.lower()
            or key in v.brand.lower()
            or key in v.model.lower()
        ]

    def filter_vehicles(
        self,
        status: str | None = None,
        type_name: str | None = None,
        branch_id: str | None = None,
    ) -> list[Vehicle]:
        result = self._vehicles
        if status:
            result = [v for v in result if v.status == status]
        if type_name:
            result = [v for v in result if v.type_name == type_name]
        if branch_id:
            result = [v for v in result if v.branch_id == branch_id]
        return list(result)

    def search_customers(self, text: str) -> list[Customer]:
        key = text.strip().lower()
        return [
            c for c in self._customers
            if key in c.name.lower()
            or key in c.phone
            or key in c.license_no.lower()
            or key in c.customer_id.lower()
        ]

    def search_rentals(self, text: str) -> list[Rental]:
        key = text.strip().lower()
        return [
            r for r in self._rentals
            if key in r.rental_id.lower()
            or key in r.customer.name.lower()
            or key in r.vehicle.plate.lower()
        ]

    def filter_rentals(
        self,
        status: str | None = None,
        payment: str | None = None,
        today: date | None = None,
    ) -> list[Rental]:
        #  status: active / returned / overdue. 
        #  payment: paid / unpaid
        today = self._today(today)
        result = self._rentals
        if status == "active":
            result = [r for r in result if r.is_active()]
        elif status == "returned":
            result = [r for r in result if not r.is_active()]
        elif status == "overdue":
            result = [r for r in result if r.is_overdue(today)]
        elif status:
            raise ValueError(f"فلتر الحالة غير معروف: {status}")

        if payment == "paid":
            result = [r for r in result if r.is_fully_paid()]
        elif payment == "unpaid":
            result = [r for r in result if not r.is_fully_paid()]
        elif payment:
            raise ValueError(f"فلتر الدفع غير معروف: {payment}")
        return list(result)

    def rentals_of_customer(self, customer_id: str) -> list[Rental]:
        customer = self.get_customer(customer_id)
        return [r for r in self._rentals if r.customer is customer]

    def rentals_of_vehicle(self, plate: str) -> list[Rental]:
        vehicle = self.get_vehicle(plate)
        return [r for r in self._rentals if r.vehicle is vehicle]

    # 6) ___________________ Dashboard Stats ___________________________

    def get_dashboard_stats(self, today: date | None = None) -> dict[str, float | int]:
        today = self._today(today)
        payments = [p for r in self._rentals for p in r.payments]
        month_revenue = sum(
            p.amount for p in payments
            if p.payment_date.year == today.year
            and p.payment_date.month == today.month
        )
        return {
            "total_vehicles": len(self._vehicles),
            "available_vehicles": sum(v.status == Vehicle.AVAILABLE for v in self._vehicles),
            "rented_vehicles": sum(v.status == Vehicle.RENTED for v in self._vehicles),
            "maintenance_vehicles": sum(v.status == Vehicle.MAINTENANCE for v in self._vehicles),
            "total_customers": len(self._customers),
            "active_rentals": sum(r.is_active() for r in self._rentals),
            "overdue_rentals": sum(r.is_overdue(today) for r in self._rentals),
            "month_revenue": round(month_revenue, 2),
            "total_revenue": round(sum(p.amount for p in payments), 2),
            "outstanding": round(sum(r.remaining() for r in self._rentals), 2),
        }

    def export_rentals_csv(self, file_path: str) -> int:
        
        headers = [
            "Rental ID", "Customer", "Plate", "Type", "Start", "End",
            "Returned", "Status", "Days", "Cost", "Late Fee",
            "Total Due", "Paid", "Remaining",
        ]
        rows = [
            [
                r.rental_id, r.customer.name, r.vehicle.plate, r.vehicle.type_name,
                r.start_date.isoformat(), r.end_date.isoformat(),
                r.returned_on.isoformat() if r.returned_on else "",
                r.status, r.days, r.calculate_cost(), r.calculate_late_fee(),
                r.total_due(), r.total_paid(), r.remaining(),
            ]
            for r in self._rentals
        ]
        self._fm.export_csv(file_path, headers, rows)
        return len(rows)

    # ==================================================================
    # ______________________ save / load (JSON) _______________________ 
    # ==================================================================
    def save(self) -> None:
        self._fm.write_json(self.BRANCHES_FILE, [b.to_dict() for b in self._branches])
        self._fm.write_json(self.VEHICLES_FILE, [v.to_dict() for v in self._vehicles])
        self._fm.write_json(self.CUSTOMERS_FILE, [c.to_dict() for c in self._customers])
        self._fm.write_json(self.RENTALS_FILE, [r.to_dict() for r in self._rentals])

    def load(self) -> None:
        #الترتيب مهم: الإيجارات بتعتمد على السيارات والعملاء، فنحمّلهم الأول

        branches = [Branch.from_dict(d) for d in self._fm.read_json(self.BRANCHES_FILE)]
        vehicles = [Vehicle.from_dict(d) for d in self._fm.read_json(self.VEHICLES_FILE)]
        customers = [Customer.from_dict(d) for d in self._fm.read_json(self.CUSTOMERS_FILE)]

        vehicles_by_plate = {v.plate: v for v in vehicles}
        customers_by_id = {c.customer_id: c for c in customers}
        rentals = [
            Rental.from_dict(d, vehicles_by_plate, customers_by_id)
            for d in self._fm.read_json(self.RENTALS_FILE)
        ]

        # نخزن القوائم في  object 
        self._branches, self._vehicles = branches, vehicles
        self._customers, self._rentals = customers, rentals