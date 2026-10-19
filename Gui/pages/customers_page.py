
from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Callable

import customtkinter as ctk

from Gui.pages.base_page import BasePage
from Gui.widgets import DataTable, LabeledEntry, SearchFilterBar
from Services.car_rentel import CarRental


class CustomersPage(BasePage):
    TITLE: str = "Customers"

    LICENSE_FILTER: list[str] = ["All", "Valid", "Expired"]

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
            placeholder="Search name, phone, license or ID...",
            filters={"License": self.LICENSE_FILTER},
        )
        self._bar.pack(fill="x", padx=24, pady=(0, 8))

        self._table = DataTable(
            self,
            columns=[
                ("id", "ID", 70),
                ("name", "Name", 170),
                ("phone", "Phone", 120),
                ("license_no", "License no.", 110),
                ("expiry", "License expiry", 110),
                ("license_status", "License", 80),
                ("rentals", "Rentals", 70),
            ],
            height=8,
            empty_text="No customers found",
            on_select=self._on_row_select,
        )
        self._table.pack(fill="both", expand=True, padx=24, pady=(0, 10))

        self._build_form()
        self._set_mode(None)

   
    # بناء الفورم
    
    def _build_form(self) -> None:
        form = ctk.CTkFrame(
            self, corner_radius=8, border_width=1, border_color=("gray80", "gray30")
        )
        form.pack(fill="x", padx=24, pady=(0, 18))

        fields = ctk.CTkFrame(form, fg_color="transparent")
        fields.pack(fill="x", padx=12, pady=(12, 6))

        self._name = LabeledEntry(fields, "Name", "Mona Ali", width=180)
        self._name.grid(row=0, column=0, padx=6, sticky="w")
        self._phone = LabeledEntry(fields, "Phone", "01012345678", width=150)
        self._phone.grid(row=0, column=1, padx=6, sticky="w")
        self._license_no = LabeledEntry(fields, "License no.", "L123", width=120)
        self._license_no.grid(row=0, column=2, padx=6, sticky="w")
        self._expiry = LabeledEntry(fields, "License expiry (YYYY-MM-DD)", "2028-01-01", width=190)
        self._expiry.grid(row=0, column=3, padx=6, sticky="w")

        buttons = ctk.CTkFrame(form, fg_color="transparent")
        buttons.pack(fill="x", padx=12, pady=(6, 4))

        self._add_btn = ctk.CTkButton(buttons, text="Add", width=90, command=self._on_add)
        self._update_btn = ctk.CTkButton(buttons, text="Update", width=90, command=self._on_update)
        self._delete_btn = ctk.CTkButton(
            buttons, text="Delete", width=90, fg_color="#D64545",
            hover_color="#B03636", command=self._on_delete,
        )
        self._history_btn = ctk.CTkButton(
            buttons, text="View rentals", width=110, fg_color="#7A869A",
            hover_color="#5F6B7D", command=self._on_view_rentals,
        )
        self._clear_btn = ctk.CTkButton(
            buttons, text="Clear", width=80, fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"), command=self._clear_form,
        )
        for button in (
            self._add_btn, self._update_btn, self._delete_btn,
            self._history_btn, self._clear_btn,
        ):
            button.pack(side="left", padx=(0, 8))

        self._status = ctk.CTkLabel(form, text="", anchor="w")
        self._status.pack(fill="x", padx=14, pady=(2, 10))

    
    # عرض البيانات
   
    def refresh(self) -> None:
        self._reload_table()

    def _reload_table(self) -> None:
        text = self._bar.search_text
        customers = (
            self._car_rental.search_customers(text)
            if text
            else self._car_rental.customers
        )

        today = date.today()
        license_filter = self._bar.filter_value("License")
        if license_filter == "Valid":
            customers = [c for c in customers if c.is_license_valid(today)]
        elif license_filter == "Expired":
            customers = [c for c in customers if not c.is_license_valid(today)]

        
        rental_counts = Counter(r.customer.customer_id for r in self._car_rental.rentals)

        rows = [
            (
                c.customer_id,
                (
                    c.customer_id,
                    c.name,
                    c.phone,
                    c.license_no,
                    c.license_expiry.isoformat(),
                    "valid" if c.is_license_valid(today) else "expired",
                    rental_counts.get(c.customer_id, 0),
                ),
            )
            for c in customers
        ]
        self._table.set_rows(rows)

    
    # أوضاع الفورم: إضافة (مفيش صف مختار) / تعديل (فيه صف مختار)
   
    def _set_mode(self, customer_id: str | None) -> None:
        editing = customer_id is not None
        self._add_btn.configure(state="disabled" if editing else "normal")
        for button in (self._update_btn, self._delete_btn, self._history_btn):
            button.configure(state="normal" if editing else "disabled")

    def _on_row_select(self, customer_id: str | None) -> None:
        if customer_id is None:
            self._selected = None
            self._set_mode(None)
            return
        try:
            customer = self._car_rental.get_customer(customer_id)
        except ValueError:
            return
        self._selected = customer_id
        self._name.set(customer.name)
        self._phone.set(customer.phone)
        self._license_no.set(customer.license_no)
        self._expiry.set(customer.license_expiry.isoformat())
        self._set_mode(customer_id)
        self._set_status("")

    def _clear_form(self) -> None:
        self._table.clear_selection()
        self._selected = None
        self._set_mode(None)
        for entry in (self._name, self._phone, self._license_no, self._expiry):
            entry.clear()
        self._set_status("")

   
    # دوال مساعدة
    
    @staticmethod
    def _parse_date(text: str) -> date:
        try:
            return date.fromisoformat(text)
        except ValueError:
            raise ValueError("تاريخ انتهاء الرخصة يجب أن يكون بصيغة YYYY-MM-DD") from None

    def _need_selection(self) -> str:
        if self._selected is None:
            raise ValueError("اختر عميلاً من الجدول أولاً")
        return self._selected

    def _set_status(self, text: str, error: bool = False) -> None:
        self._status.configure(text=text, text_color="#D64545" if error else "#2E9E5B")

    def _fail(self, error: Exception) -> None:
        self._set_status(str(error), error=True)
        self.show_error(error)

    def _done(self, message: str) -> None:
        self._clear_form()
        self._reload_table()
        self._set_status(message)

   
    # الأزرار

    def _on_add(self) -> None:
        try:
            customer = self._car_rental.add_customer(
                self._name.get(),
                self._phone.get(),
                self._license_no.get(),
                self._parse_date(self._expiry.get()),
            )
        except ValueError as e:
            self._fail(e)
            return
        self._done(f"Added {customer.customer_id} - {customer.name}")

    def _on_update(self) -> None:
        try:
            customer_id = self._need_selection()
            self._car_rental.update_customer(
                customer_id,
                self._name.get(),
                self._phone.get(),
                self._license_no.get(),
                self._parse_date(self._expiry.get()),
            )
        except ValueError as e:
            self._fail(e)
            return
        self._done(f"Updated {customer_id}")

    def _on_delete(self) -> None:
        try:
            customer_id = self._need_selection()
            if not self.confirm(f"Delete customer {customer_id}?"):
                return
            self._car_rental.delete_customer(customer_id)
        except ValueError as e:
            self._fail(e)
            return
        self._done(f"Deleted {customer_id}")

    def _on_view_rentals(self) -> None:
      
        try:
            customer_id = self._need_selection()
            customer = self._car_rental.get_customer(customer_id)
            rentals = self._car_rental.rentals_of_customer(customer_id)
        except ValueError as e:
            self._fail(e)
            return

        window = ctk.CTkToplevel(self)
        window.title(f"Rentals of {customer.name}")
        window.geometry("760x340")
        ctk.CTkLabel(
            window,
            text=f"{customer.name} ({customer.customer_id})",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 6))

        table = DataTable(
            window,
            columns=[
                ("id", "Rental", 70),
                ("plate", "Plate", 90),
                ("start", "Start", 100),
                ("end", "End", 100),
                ("status", "Status", 80),
                ("due", "Total due", 100),
                ("remaining", "Remaining", 100),
            ],
            height=8,
            empty_text="No rentals for this customer",
        )
        table.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        table.set_rows(
            [
                (
                    r.rental_id,
                    (
                        r.rental_id,
                        r.vehicle.plate,
                        r.start_date.isoformat(),
                        r.end_date.isoformat(),
                        r.status,
                        f"{r.total_due():,.2f}",
                        f"{r.remaining():,.2f}",
                    ),
                )
                for r in rentals
            ]
        )
        window.after(100, window.lift)  