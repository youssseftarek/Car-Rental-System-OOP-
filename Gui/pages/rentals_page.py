
from __future__ import annotations

from datetime import date, timedelta
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from Gui.pages.base_page import BasePage
from Gui.widgets import DataTable, LabeledEntry, SearchFilterBar
from Services.car_rentel import CarRental


class RentalsPage(BasePage):
    TITLE: str = "Rentals"

    STATUS_FILTER: list[str] = ["All", "active", "returned", "overdue"]
    PAYMENT_FILTER: list[str] = ["All", "paid", "unpaid"]
    NO_VEHICLES: str = "(no available vehicles)"
    NO_CUSTOMERS: str = "(no customers)"

    def __init__(
        self,
        parent: ctk.CTkFrame,
        car_rental: CarRental,
        navigate: Callable[[str], None],
    ) -> None:
        super().__init__(parent, car_rental, navigate)
        self._selected: str | None = None  
        
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(0, 8))
        self._bar = SearchFilterBar(
            top,
            on_change=self._reload_table,
            placeholder="Search rental, customer or plate...",
            filters={"Status": self.STATUS_FILTER, "Payment": self.PAYMENT_FILTER},
        )
        self._bar.pack(side="left")
        ctk.CTkButton(
            top, text="Export CSV", width=110, command=self._on_export
        ).pack(side="right")

        # --- الجدول ---
        self._table = DataTable(
            self,
            columns=[
                ("id", "Rental", 60),
                ("customer", "Customer", 130),
                ("plate", "Plate", 80),
                ("start", "Start", 85),
                ("end", "End", 85),
                ("returned", "Returned", 85),
                ("status", "Status", 75),
                ("cost", "Cost", 80),
                ("late", "Late fee", 75),
                ("paid", "Paid", 80),
                ("remaining", "Remaining", 85),
            ],
            height=6,
            empty_text="No rentals found",
            on_select=self._on_row_select,
        )
        self._table.pack(fill="both", expand=True, padx=24, pady=(0, 10))

        self._build_panels()
        self._status = ctk.CTkLabel(self, text="", anchor="w")
        self._status.pack(fill="x", padx=26, pady=(0, 10))

        self._reset_form()
        self._set_selected_mode(selected=False, active=False)

 
    # بناء الفورم: كارت "إيجار جديد" وكارت "الإيجار المختار"
  
    def _build_panels(self) -> None:
        panels = ctk.CTkFrame(self, fg_color="transparent")
        panels.pack(fill="x", padx=24, pady=(0, 4))
        panels.grid_columnconfigure(0, weight=3)
        panels.grid_columnconfigure(1, weight=2)
        border = ("gray80", "gray30")

        # ----- إيجار جديد -----
        new_card = ctk.CTkFrame(panels, corner_radius=8, border_width=1, border_color=border)
        new_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(
            new_card, text="New rental", font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=12, pady=(10, 2))

        fields = ctk.CTkFrame(new_card, fg_color="transparent")
        fields.pack(fill="x", padx=6, pady=(0, 4))
        self._vehicle_menu = self._menu_field(fields, "Vehicle (available only)", 250, 0)
        self._customer_menu = self._menu_field(fields, "Customer", 170, 1)
        self._start = LabeledEntry(fields, "Start (YYYY-MM-DD)", width=120)
        self._start.grid(row=0, column=2, padx=6, sticky="w")
        self._end = LabeledEntry(fields, "End (YYYY-MM-DD)", width=120)
        self._end.grid(row=0, column=3, padx=6, sticky="w")

        buttons = ctk.CTkFrame(new_card, fg_color="transparent")
        buttons.pack(fill="x", padx=12, pady=(2, 2))
        ctk.CTkButton(
            buttons, text="Preview cost", width=110, fg_color="#7A869A",
            hover_color="#5F6B7D", command=self._on_preview,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(buttons, text="Rent", width=90, command=self._on_rent).pack(side="left")
        self._estimate = ctk.CTkLabel(new_card, text="", anchor="w")
        self._estimate.pack(fill="x", padx=14, pady=(2, 10))

        # ----- الإيجار المختار (إرجاع) -----
        sel_card = ctk.CTkFrame(panels, corner_radius=8, border_width=1, border_color=border)
        sel_card.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(
            sel_card, text="Selected rental", font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=12, pady=(10, 2))
        self._info = ctk.CTkLabel(
            sel_card, text="", anchor="w", justify="left", wraplength=330
        )
        self._info.pack(fill="x", padx=14, pady=(0, 4))

        row = ctk.CTkFrame(sel_card, fg_color="transparent")
        row.pack(fill="x", padx=6, pady=(0, 10))
        self._return_date = LabeledEntry(row, "Return date (YYYY-MM-DD)", width=150)
        self._return_date.pack(side="left", padx=6)
        self._return_btn = ctk.CTkButton(
            row, text="Return car", width=100, command=self._on_return
        )
        self._return_btn.pack(side="left", padx=(6, 6), pady=(18, 0))
        self._payments_btn = ctk.CTkButton(
            row, text="Payments", width=90, fg_color="#7A869A", hover_color="#5F6B7D",
            command=lambda: self._navigate("payments"),
        )
        self._payments_btn.pack(side="left", pady=(18, 0))

    @staticmethod
    def _menu_field(
        parent: ctk.CTkFrame, label: str, width: int, column: int
    ) -> ctk.CTkOptionMenu:
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=0, column=column, padx=6, sticky="w")
        ctk.CTkLabel(box, text=label, anchor="w").pack(fill="x")
        menu = ctk.CTkOptionMenu(box, values=["-"], width=width, dynamic_resizing=False)
        menu.pack(fill="x")
        return menu

    
    # عرض البيانات
    
    def refresh(self) -> None:
        vehicles = self._car_rental.filter_vehicles(status="available")
        self._set_menu(
            self._vehicle_menu,
            [f"{v.plate} - {v.brand} {v.model} ({v.type_name})" for v in vehicles]
            or [self.NO_VEHICLES],
        )
        customers = self._car_rental.customers
        self._set_menu(
            self._customer_menu,
            [f"{c.customer_id} - {c.name}" for c in customers] or [self.NO_CUSTOMERS],
        )
        self._reload_table()

    @staticmethod
    def _set_menu(menu: ctk.CTkOptionMenu, labels: list[str]) -> None:
        current = menu.get()
        menu.configure(values=labels)
        menu.set(current if current in labels else labels[0])

    def _reload_table(self) -> None:
        today = date.today()
        status = self._bar.filter_value("Status")
        payment = self._bar.filter_value("Payment")
        rentals = self._car_rental.filter_rentals(
            status=None if status == "All" else status,
            payment=None if payment == "All" else payment,
            today=today,
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
                    r.start_date.isoformat(),
                    r.end_date.isoformat(),
                    r.returned_on.isoformat() if r.returned_on else "-",
                    "overdue" if r.is_overdue(today) else r.status,
                    f"{r.calculate_cost():,.2f}",
                    f"{r.calculate_late_fee():,.2f}",
                    f"{r.total_paid():,.2f}",
                    f"{r.remaining():,.2f}",
                ),
            )
            for r in reversed(rentals)  
        ]
        self._table.set_rows(rows)


    # اختيار صف
  
    def _on_row_select(self, rental_id: str | None) -> None:
        if rental_id is None:
            self._selected = None
            self._info.configure(text="Select a rental from the table.")
            self._set_selected_mode(selected=False, active=False)
            return
        try:
            rental = self._car_rental.get_rental(rental_id)
        except ValueError:
            return
        self._selected = rental_id
        self._info.configure(
            text=(
                f"{rental.rental_id}  |  {rental.customer.name}  |  {rental.vehicle.plate}\n"
                f"Due {rental.total_due():,.2f}   Paid {rental.total_paid():,.2f}   "
                f"Remaining {rental.remaining():,.2f}"
            )
        )
        self._return_date.set(date.today().isoformat())
        self._set_selected_mode(selected=True, active=rental.is_active())
        self._set_status("")

    def _set_selected_mode(self, selected: bool, active: bool) -> None:
        """الإرجاع متاح للإيجار النشط بس، وزرار Payments لأي إيجار مختار."""
        self._return_date.set_enabled(active)
        self._return_btn.configure(state="normal" if active else "disabled")
        self._payments_btn.configure(state="normal" if selected else "disabled")

    def _reset_form(self) -> None:
        today = date.today()
        self._start.set(today.isoformat())
        self._end.set((today + timedelta(days=1)).isoformat())
        self._estimate.configure(text="")
        self._info.configure(text="Select a rental from the table.")

    
    # دوال مساعدة
   
    @staticmethod
    def _parse_date(text: str, field: str) -> date:
        try:
            return date.fromisoformat(text)
        except ValueError:
            raise ValueError(f"{field} يجب أن يكون بصيغة YYYY-MM-DD") from None

    def _read_rent_inputs(self) -> tuple[str, str, date, date]:
        vehicle_text = self._vehicle_menu.get()
        customer_text = self._customer_menu.get()
        if vehicle_text == self.NO_VEHICLES:
            raise ValueError("لا توجد سيارات متاحة للتأجير")
        if customer_text == self.NO_CUSTOMERS:
            raise ValueError("سجّل عميلاً أولاً من صفحة Customers")
        plate = vehicle_text.split(" - ")[0]
        customer_id = customer_text.split(" - ")[0]
        start = self._parse_date(self._start.get(), "تاريخ الاستلام")
        end = self._parse_date(self._end.get(), "تاريخ الإرجاع")
        return plate, customer_id, start, end

    def _need_selection(self) -> str:
        if self._selected is None:
            raise ValueError("اختر إيجاراً من الجدول أولاً")
        return self._selected

    def _set_status(self, text: str, error: bool = False) -> None:
        self._status.configure(text=text, text_color="#D64545" if error else "#2E9E5B")

    def _fail(self, error: Exception) -> None:
        self._set_status(str(error), error=True)
        self.show_error(error)

    def _done(self, message: str) -> None:
        self._table.clear_selection()
        self._selected = None
        self._reset_form()
        self._set_selected_mode(selected=False, active=False)
        self.refresh() 
        self._set_status(message)

   
    # الأزرار
  
    def _on_preview(self) -> None:
        try:
            plate, customer_id, start, end = self._read_rent_inputs()
            cost = self._car_rental.estimate_rental_cost(plate, customer_id, start, end)
        except ValueError as e:
            self._fail(e)
            return
        self._estimate.configure(text=f"Estimated cost: {cost:,.2f} EGP")
        self._set_status("")

    def _on_rent(self) -> None:
        try:
            plate, customer_id, start, end = self._read_rent_inputs()
            cost = self._car_rental.estimate_rental_cost(plate, customer_id, start, end)
            customer = self._car_rental.get_customer(customer_id)
            if not self.confirm(
                f"Rent {plate} to {customer.name}?\n"
                f"{start.isoformat()}  to  {end.isoformat()}\n"
                f"Estimated cost: {cost:,.2f} EGP"
            ):
                return
            rental = self._car_rental.rent_car(plate, customer_id, start, end)
        except ValueError as e:
            self._fail(e)
            return
        self._done(f"Created {rental.rental_id}: {rental.calculate_cost():,.2f} EGP")

    def _on_return(self) -> None:
        try:
            rental_id = self._need_selection()
            rental = self._car_rental.get_rental(rental_id)
            return_date = self._parse_date(self._return_date.get(), "تاريخ الإرجاع")
            late_fee = rental.calculate_late_fee(return_date)  # معاينة قبل التأكيد
            total = round(rental.calculate_cost() + late_fee, 2)
            if not self.confirm(
                f"Return {rental.vehicle.plate} on {return_date.isoformat()}?\n"
                f"Late fee: {late_fee:,.2f} EGP\n"
                f"Total due: {total:,.2f} EGP\n"
                f"Paid so far: {rental.total_paid():,.2f} EGP"
            ):
                return
            self._car_rental.return_car(rental_id, return_date)
        except ValueError as e:
            self._fail(e)
            return
        self._done(f"Returned {rental_id}. Remaining to pay: {rental.remaining():,.2f} EGP")

    def _on_export(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="rentals_report.csv",
        )
        if not path: 
            return
        try:
            count = self._car_rental.export_rentals_csv(path)
        except ValueError as e:
            self._fail(e)
            return
        self._set_status(f"Exported {count} rental(s)")
        self.show_info(f"Exported {count} rental(s) to:\n{path}")