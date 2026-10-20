"""tests/run_scenarios.py: يشغّل الـ 10 سيناريوهات ويطبع PASS أو FAIL."""
from __future__ import annotations

import sys
import tempfile
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Callable, Iterator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from File_Manger.File_manger import FileManager
from Services.car_rentel import CarRental

TODAY = date(2027, 1, 1)  


@contextmanager
def system() -> Iterator[CarRental]:
   
    with tempfile.TemporaryDirectory() as tmp:
        cr = CarRental(FileManager(Path(tmp) / "data"))
        cr.add_branch("Cairo Branch", "Nasr City")
        cr.add_vehicle("EconomyCar", "abc123", "Toyota", "Yaris", 400, "B01")
        cr.add_customer("Mona Ali", "01012345678", "L123", date(2028, 1, 1))
        yield cr


def must_fail(action: Callable[[], object]) -> str:
   
    try:
        action()
    except ValueError as e:
        return str(e)
    raise AssertionError("البرنامج قبل العملية وكان لازم يرفضها")


# ---------------- 3 سيناريوهات ناجحة ----------------
def s1() -> str:
    with system() as cr:
        cr.add_vehicle("SUV", "xyz789", "Kia", "Sportage", 500, "B01")
        assert cr.get_vehicle("xyz789").status == "available"
        assert len(cr.vehicles) == 2
        return "vehicle added, status=available, total vehicles=2"


def s2() -> str:
    with system() as cr:
        r = cr.rent_car("abc123", "C001", date(2027, 1, 1), date(2027, 1, 4), today=TODAY)
        assert r.calculate_cost() == 1260.0
        assert cr.get_vehicle("abc123").status == "rented"
        return f"{r.rental_id} created, cost={r.calculate_cost()}, car=rented"


def s3() -> str:
    with system() as cr:
        r = cr.rent_car("abc123", "C001", date(2027, 1, 1), date(2027, 1, 4), today=TODAY)
        cr.return_car(r.rental_id, date(2027, 1, 4), today=date(2027, 1, 4))
        assert r.status == "returned"
        assert r.calculate_late_fee() == 0.0
        assert cr.get_vehicle("abc123").status == "available"
        return "status=returned, late fee=0.0, car=available"


# ---------------- 3 سيناريوهات مدخلات غير صالحة ----------------
def s4() -> str:
    with system() as cr:
        msg = must_fail(lambda: cr.add_vehicle("SUV", "neg1", "Kia", "X", -50, "B01"))
        assert len(cr.vehicles) == 1
        return f"rejected: {msg}"


def s5() -> str:
    with system() as cr:
        msg = must_fail(lambda: cr.add_customer("Ahmed", "", "L999", date(2028, 1, 1)))
        assert len(cr.customers) == 1
        return f"rejected: {msg}"


def s6() -> str:
    with system() as cr:
        r = cr.rent_car("abc123", "C001", date(2027, 1, 1), date(2027, 1, 4), today=TODAY)
        msg = must_fail(lambda: cr.record_payment(r.rental_id, 100, "bitcoin", TODAY))
        assert r.total_paid() == 0
        return f"rejected: {msg}"


# ---------------- 2 سيناريوهات مخالفة قاعدة شغل ----------------
def s7() -> str:
    with system() as cr:
        cr.rent_car("abc123", "C001", date(2027, 1, 1), date(2027, 1, 4), today=TODAY)
        msg = must_fail(
            lambda: cr.rent_car("abc123", "C001", date(2027, 1, 5), date(2027, 1, 6), today=TODAY)
        )
        assert len(cr.rentals) == 1
        return f"rejected: {msg}"


def s8() -> str:
    with system() as cr:
        msg = must_fail(
            lambda: cr.rent_car("abc123", "C001", date(2027, 1, 5), date(2027, 1, 1), today=TODAY)
        )
        assert cr.get_vehicle("abc123").status == "available"
        return f"rejected: {msg}"


# ---------------- 2 سيناريوهات حالات حدّية ----------------
def s9() -> str:
    with system() as cr:
        r = cr.rent_car("abc123", "C001", date(2027, 2, 1), date(2027, 2, 1), today=TODAY)
        assert r.days == 1
        assert r.calculate_cost() == 420.0
        return f"same-day rental: days={r.days}, cost={r.calculate_cost()}"


def s10() -> str:
    with system() as cr:
        cr.add_customer("Sara Mahmoud", "01155554444", "L777", date(2027, 1, 4))
        r = cr.rent_car("abc123", "C002", date(2027, 1, 1), date(2027, 1, 4), today=TODAY)
        assert r.status == "active"
        return "license expiring on the last rental day is accepted"


SCENARIOS: list[tuple[int, str, str, Callable[[], str]]] = [
    (1, "Success", "Add a vehicle", s1),
    (2, "Success", "Rent an available car", s2),
    (3, "Success", "Return a car on time", s3),
    (4, "Invalid input", "Negative vehicle price", s4),
    (5, "Invalid input", "Empty customer phone", s5),
    (6, "Invalid input", "Unknown payment method", s6),
    (7, "Business rule", "Rent an already rented car", s7),
    (8, "Business rule", "Return date before start date", s8),
    (9, "Edge case", "Same-day rental counts as 1 day", s9),
    (10, "Edge case", "License expires on the last rental day", s10),
]


def main() -> int:
    passed = 0
    for number, kind, title, func in SCENARIOS:
        try:
            actual = func()
            verdict = "PASS"
            passed += 1
        except AssertionError as e:
            actual, verdict = f"assertion failed: {e}", "FAIL"
        except Exception as e:  # أي خطأ غير متوقع
            actual, verdict = f"unexpected {type(e).__name__}: {e}", "FAIL"
        print(f"[{verdict}] #{number:<2} {kind:<13} {title}")
        print(f"        actual: {actual}")
    print(f"\n{passed}/{len(SCENARIOS)} scenarios passed")
    return 0 if passed == len(SCENARIOS) else 1


if __name__ == "__main__":
    sys.exit(main())