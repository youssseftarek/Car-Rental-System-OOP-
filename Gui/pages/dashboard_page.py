
from __future__ import annotations

from datetime import date
from typing import Callable

import customtkinter as ctk

from Gui.pages.base_page import BasePage
from Gui.widgets import DataTable, StatCard
from Services.car_rentel import CarRental


class DashboardPage(BasePage):
    TITLE: str = "Dashboard"


    CARDS: list[tuple[str, str, str, bool]] = [
        ("total_vehicles", "Total vehicles", "#3B8ED0", False),
        ("available_vehicles", "Available", "#2E9E5B", False),
        ("rented_vehicles", "Rented", "#E08A1E", False),
        ("maintenance_vehicles", "In maintenance", "#7A869A", False),
        ("total_customers", "Customers", "#3B8ED0", False),
        ("active_rentals", "Active rentals", "#E08A1E", False),
        ("overdue_rentals", "Overdue rentals", "#D64545", False),
        ("month_revenue", "This month (EGP)", "#2E9E5B", True),
        ("total_revenue", "Total revenue (EGP)", "#2E9E5B", True),
        ("outstanding", "Outstanding (EGP)", "#D64545", True),
    ]
    COLUMNS_PER_ROW: int = 5
    RECENT_COUNT: int = 8

    def __init__(
        self,
        parent: ctk.CTkFrame,
        car_rental: CarRental,
        navigate: Callable[[str], None],
    ) -> None:
        super().__init__(parent, car_rental, navigate)

        # --- الكروت ---
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=18, pady=(4, 12))
        for column in range(self.COLUMNS_PER_ROW):
            cards_frame.grid_columnconfigure(column, weight=1, uniform="cards")

        self._cards: dict[str, StatCard] = {}
        for index, (key, title, accent, _is_money) in enumerate(self.CARDS):
            card = StatCard(cards_frame, title, "0", accent)
            card.grid(
                row=index // self.COLUMNS_PER_ROW,
                column=index % self.COLUMNS_PER_ROW,
                sticky="nsew",
                padx=6,
                pady=6,
            )
            self._cards[key] = card

        # --- جدول آخر الإيجارات ---
        ctk.CTkLabel(
            self, text="Recent rentals", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=24, pady=(4, 6))

        self._table = DataTable(
            self,
            columns=[
                ("id", "Rental", 80),
                ("customer", "Customer", 170),
                ("plate", "Plate", 100),
                ("start", "Start", 100),
                ("end", "End", 100),
                ("status", "Status", 90),
                ("remaining", "Remaining (EGP)", 130),
            ],
            height=self.RECENT_COUNT,
            empty_text="No rentals yet",
        )
        self._table.pack(fill="both", expand=True, padx=24, pady=(0, 20))

    def refresh(self) -> None:
        stats = self._car_rental.get_dashboard_stats()
        for key, _title, _accent, is_money in self.CARDS:
            value = stats[key]
            self._cards[key].set_value(f"{value:,.2f}" if is_money else str(value))

        today = date.today()
        latest = list(reversed(self._car_rental.rentals))[: self.RECENT_COUNT]
        rows = [
            (
                r.rental_id,
                (
                    r.rental_id,
                    r.customer.name,
                    r.vehicle.plate,
                    r.start_date.isoformat(),
                    r.end_date.isoformat(),
                    "overdue" if r.is_overdue(today) else r.status,
                    f"{r.remaining():,.2f}",
                ),
            )
            for r in latest
        ]
        self._table.set_rows(rows)