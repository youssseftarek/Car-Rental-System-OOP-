
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from Gui.pages.base_page import BasePage
from Gui.widgets import DataTable, LabeledEntry, SearchFilterBar
from Models.payment import Payment
from Services.car_rentel import CarRental


class PaymentsPage(BasePage):
    TITLE: str = "Payments"

    PAYMENT_FILTER: list[str] = ["All", "paid", "unpaid"]
    METHODS: list[str] = list(Payment.VALID_METHODS)

    def __init__(
        self,
        parent: ctk.CTkFrame,
        car_rental: CarRental,
        navigate: Callable[[str], None],
    ) -> None:
        super().__init__(parent, car_rental, navigate)
        self._selected: str | None = None 

        self._bar = SearchFilterBar(
            self,
            on_change=self._reload_table,
            placeholder="Search rental, customer or plate...",
            filters={"Payment": self.PAYMENT_FILTER},
        )
        self._bar.pack(fill="x", padx=24, pady=(0, 8))

        self._rentals_table = DataTable(
            self,
            columns=[
                ("id", "Rental", 70),
                ("customer", "Customer", 150),
                ("plate", "Plate", 90),
                ("status", "Status", 80),
                ("due", "Total due", 100),
                ("paid", "Paid", 100),
                ("remaining", "Remaining", 100),
                ("state", "Payment", 80),
            ],
            height=6,
            empty_text="No rentals found",
            on_select=self._on_row_select,
        )
        self._rentals_table.pack(fill="both", expand=True, padx=24, pady=(0, 10))

        self._build_bottom()
        self._status = ctk.CTkLabel(self, text="", anchor="w")
        self._status.pack(fill="x", padx=26, pady=(0, 10))

        self._set_selected_mode(False)


    # بناء الجزء السفلي: كارت تسجيل الدفعة + جدول دفعات الإيجار المختار
   
    def _build_bottom(self) -> None:
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=24, pady=(0, 4))
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)
        border = ("gray80", "gray30")

        # ----- تسجيل دفعة -----
        card = ctk.CTkFrame(bottom, corner_radius=8, border_width=1, border_color=border)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(
            card, text="Record payment", font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=12, pady=(10, 2))

        self._summary = ctk.CTkLabel(
            card, text="", anchor="w", justify="left", wraplength=380
        )
        self._summary.pack(fill="x", padx=14, pady=(0, 6))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=6, pady=(0, 4))
        self._amount = LabeledEntry(row, "Amount (EGP)", "1000", width=120)
        self._amount.pack(side="left", padx=6)

        method_box = ctk.CTkFrame(row, fg_color="transparent")
        method_box.pack(side="left", padx=6)
        ctk.CTkLabel(method_box, text="Method", anchor="w").pack(fill="x")
        self._method = ctk.CTkOptionMenu(method_box, values=self.METHODS, width=120)
        self._method.pack(fill="x")

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.pack(fill="x", padx=12, pady=(4, 12))
        self._pay_btn = ctk.CTkButton(
            buttons, text="Record payment", width=130, command=self._on_pay
        )
        self._pay_btn.pack(side="left", padx=(0, 8))
        self._full_btn = ctk.CTkButton(
            buttons, text="Pay full remaining", width=140, fg_color="#7A869A",
            hover_color="#5F6B7D", command=self._on_fill_remaining,
        )
        self._full_btn.pack(side="left")

        # ----- دفعات الإيجار المختار -----
        right = ctk.CTkFrame(bottom, corner_radius=8, border_width=1, border_color=border)
        right.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(
            right, text="Payments of selected rental", font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=12, pady=(10, 4))
        self._payments_table = DataTable(
            right,
            columns=[
                ("id", "Payment", 80),
                ("date", "Date", 100),
                ("method", "Method", 90),
                ("amount", "Amount (EGP)", 110),
            ],
            height=4,
            empty_text="No payments yet",
        )
        self._payments_table.pack(fill="both", expand=True, padx=10, pady=(0, 10))

   
    # عرض البيانات
   
    def refresh(self) -> None:
        self._reload_table()

    def _reload_table(self) -> None:
        payment = self._bar.filter_value("Payment")
        rentals = self._car_rental.filter_rentals(
            payment=None if payment == "All" else payment
        )
        text = self._bar.search_text
        if text:
            matched = {r.rental_id for r in self._car_rental.search_rentals(text)}
            rentals = [r for r in rentals if r.rental_id in matched]

        rows = [
            (
                r.rental_id,
                (
                    r.rental_id,
                    r.customer.name,
                    r.vehicle.plate,
                    r.status,
                    f"{r.total_due():,.2f}",
                    f"{r.total_paid():,.2f}",
                    f"{r.remaining():,.2f}",
                    "paid" if r.is_fully_paid() else "unpaid",
                ),
            )
            for r in reversed(rentals) 
        ]
        self._rentals_table.set_rows(rows)

        # نرجّع اختيار الإيجار لو لسه موجود في النتيجة
        if self._selected and any(row_id == self._selected for row_id, _ in rows):
            self._rentals_table.select(self._selected)
        else:
            self._selected = None
            self._show_selection(None)

  
    # اختيار صف
 
    def _on_row_select(self, rental_id: str | None) -> None:
        self._selected = rental_id
        self._show_selection(rental_id)

    def _show_selection(self, rental_id: str | None) -> None:
        if rental_id is None:
            self._summary.configure(text="Select a rental from the table.")
            self._payments_table.set_rows([])
            self._set_selected_mode(False)
            return
        try:
            rental = self._car_rental.get_rental(rental_id)
        except ValueError:
            return

        note = ""
        if rental.is_active():
            note = "\nLate fees (if any) are added when the car is returned."
        self._summary.configure(
            text=(
                f"{rental.rental_id}  |  {rental.customer.name}  |  {rental.vehicle.plate}\n"
                f"Total due: {rental.total_due():,.2f}   Paid: {rental.total_paid():,.2f}   "
                f"Remaining: {rental.remaining():,.2f}{note}"
            )
        )
        self._payments_table.set_rows(
            [
                (
                    p.payment_id,
                    (
                        p.payment_id,
                        p.payment_date.isoformat(),
                        p.method,
                        f"{p.amount:,.2f}",
                    ),
                )
                for p in rental.payments
            ]
        )
        self._set_selected_mode(True)

    def _set_selected_mode(self, selected: bool) -> None:
        state = "normal" if selected else "disabled"
        self._amount.set_enabled(selected)
        self._method.configure(state=state)
        self._pay_btn.configure(state=state)
        self._full_btn.configure(state=state)

   
    # دوال مساعدة

    @staticmethod
    def _parse_amount(text: str) -> float:
        try:
            return float(text.replace(",", ""))
        except ValueError:
            raise ValueError("المبلغ يجب أن يكون رقماً") from None

    def _need_selection(self) -> str:
        if self._selected is None:
            raise ValueError("اختر إيجاراً من الجدول أولاً")
        return self._selected

    def _set_status(self, text: str, error: bool = False) -> None:
        self._status.configure(text=text, text_color="#D64545" if error else "#2E9E5B")

    def _fail(self, error: Exception) -> None:
        self._set_status(str(error), error=True)
        self.show_error(error)

   
    # الأزرار
    
    def _on_fill_remaining(self) -> None:
        try:
            rental = self._car_rental.get_rental(self._need_selection())
        except ValueError as e:
            self._fail(e)
            return
        self._amount.set(f"{rental.remaining():.2f}")

    def _on_pay(self) -> None:
        try:
            rental_id = self._need_selection()
            payment = self._car_rental.record_payment(
                rental_id,
                self._parse_amount(self._amount.get()),
                self._method.get(),
            )
        except ValueError as e:
            self._fail(e)
            return
        self._amount.clear()
        self._reload_table()  
        self._set_status(f"Recorded {payment.payment_id}: {payment.amount:,.2f} EGP")