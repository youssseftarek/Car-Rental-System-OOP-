
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from File_Manger.File_manger import FileManager
from Services.car_rentel import CarRental

DATA_DIR = Path(__file__).resolve().parent / "Data"


def main() -> None:
    cr = CarRental(FileManager(DATA_DIR))
    cr.load()
    if cr.vehicles or cr.customers or cr.rentals:
        print("فيه داتا موجودة بالفعل، ما عملتش حاجة.")
        print("لو عايز تبدأ من الصفر: اقفل البرنامج، انسخ فولدر data كنسخة احتياطية،")
        print("وامسح ملفات json اللي جواه، وشغّل السكريبت تاني.")
        return

    today = date.today()
    d = lambda days: today + timedelta(days=days)  
    # الفروع
    if not cr.branches:
        cr.add_branch("Main Branch", "Cairo")
    cr.add_branch("Giza Branch", "Giza")

    # السيارات: 6 (نوعين لكل فئة)
    cr.add_vehicle("EconomyCar", "abc123", "Toyota", "Yaris", 400, "B01")
    cr.add_vehicle("EconomyCar", "def456", "Hyundai", "Accent", 350, "B01")
    cr.add_vehicle("SUV", "xyz789", "Kia", "Sportage", 500, "B01")
    cr.add_vehicle("SUV", "suv222", "Nissan", "Qashqai", 550, "B02")
    cr.add_vehicle("LuxuryCar", "lux001", "BMW", "520", 900, "B02")
    cr.add_vehicle("LuxuryCar", "lux002", "Mercedes", "C200", 1000, "B02")
    cr.send_to_maintenance("lux002")

    # العملاء: واحد منهم رخصته منتهية (عشان فلتر Expired)
    cr.add_customer("Mona Ali", "01012345678", "L123", d(730))
    cr.add_customer("Ahmed Hassan", "01098765432", "L456", d(365))
    cr.add_customer("Sara Mahmoud", "01155554444", "L789", d(1095))
    cr.add_customer("Omar Khaled", "01234567890", "L321", d(-30))

    # R001: رجّعت متأخر يومين، ودفعت جزء بس
    r1 = cr.rent_car("abc123", "C001", d(-10), d(-7), today=d(-10))
    cr.record_payment(r1.rental_id, 1000, "cash", d(-10))
    cr.return_car(r1.rental_id, d(-5), today=d(-5))

    # R002: رجّع في ميعاده ودفع كله
    r2 = cr.rent_car("xyz789", "C002", d(-20), d(-17), today=d(-20))
    cr.record_payment(r2.rental_id, r2.remaining(), "card", d(-20))
    cr.return_car(r2.rental_id, d(-17), today=d(-17))

    # R003: نشط، دفع جزء
    r3 = cr.rent_car("def456", "C003", d(-2), d(3), today=d(-2))
    cr.record_payment(r3.rental_id, 500, "cash", today)

    # R004: متأخر (ميعاده عدّى ولسه ما رجعتش)، دفع جزء
    r4 = cr.rent_car("lux001", "C001", d(-8), d(-4), today=d(-8))
    cr.record_payment(r4.rental_id, 3000, "transfer", today)

    print("تمام، الداتا اتحفظت في فولدر data.")
    print(cr.get_dashboard_stats(today=today))


if __name__ == "__main__":
    main()