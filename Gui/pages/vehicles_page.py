
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from Gui.pages.base_page import BasePage
from Gui.widgets import DataTable, LabeledEntry, SearchFilterBar
from Models.vehicle import VEHICLE_TYPES
from Services.car_rentel import CarRental


class VehiclesPage(BasePage):
    TITLE: str = "Vehicles"

    STATUS_FILTER: list[str] = ["All", "available", "rented", "maintenance"]
    TYPE_FILTER: list[str] = ["All", *VEHICLE_TYPES]

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
            placeholder="Search plate, brand or model...",
            filters={"Status": self.STATUS_FILTER, "Type": self.TYPE_FILTER},
        )
        self._bar.pack(fill="x", padx=24, pady=(0, 8))

        self._table = DataTable(
            self,
            columns=[
                ("plate", "Plate", 90),
                ("brand", "Brand", 100),
                ("model", "Model", 100),
                ("type", "Type", 100),
                ("base", "Base rate", 90),
                ("daily", "Daily rate", 90),
                ("insurance", "Insurance/day", 100),
                ("status", "Status", 95),
                ("branch", "Branch", 130),
            ],
            height=8,
            empty_text="No vehicles found",
            on_select=self._on_row_select,
        )
        self._table.pack(fill="both", expand=True, padx=24, pady=(0, 10))

        self._build_form()
        self._set_mode(None)

    
# Build Form  
    def _build_form(self) -> None:
        form = ctk.CTkFrame(
            self, corner_radius=8, border_width=1, border_color=("gray80", "gray30")
        )
        form.pack(fill="x", padx=24, pady=(0, 18))

        fields = ctk.CTkFrame(form, fg_color="transparent")
        fields.pack(fill="x", padx=12, pady=(12, 6))

        self._type_menu = self._menu_field(fields, "Type", list(VEHICLE_TYPES), 0)
        self._plate = LabeledEntry(fields, "Plate", "ABC123", width=120)
        self._plate.grid(row=0, column=1, padx=6, sticky="w")
        self._brand = LabeledEntry(fields, "Brand", "Toyota", width=120)
        self._brand.grid(row=0, column=2, padx=6, sticky="w")
        self._model = LabeledEntry(fields, "Model", "Yaris", width=120)
        self._model.grid(row=0, column=3, padx=6, sticky="w")
        self._rate = LabeledEntry(fields, "Base rate / day", "400", width=110)
        self._rate.grid(row=0, column=4, padx=6, sticky="w")
        self._branch_menu = self._menu_field(fields, "Branch", ["-"], 5)

        buttons = ctk.CTkFrame(form, fg_color="transparent")
        buttons.pack(fill="x", padx=12, pady=(6, 4))

        self._add_btn = ctk.CTkButton(buttons, text="Add", width=90, command=self._on_add)
        self._update_btn = ctk.CTkButton(buttons, text="Update", width=90, command=self._on_update)
        self._delete_btn = ctk.CTkButton(
            buttons, text="Delete", width=90, fg_color="#D64545",
            hover_color="#B03636", command=self._on_delete,
        )
        self._maint_btn = ctk.CTkButton(
            buttons, text="To maintenance", width=130, fg_color="#7A869A",
            hover_color="#5F6B7D", command=self._on_maintenance,
        )
        self._finish_btn = ctk.CTkButton(
            buttons, text="Finish maintenance", width=150, fg_color="#7A869A",
            hover_color="#5F6B7D", command=self._on_finish_maintenance,
        )
        self._clear_btn = ctk.CTkButton(
            buttons, text="Clear", width=80, fg_color="transparent", border_width=1,
            text_color=("gray10", "gray90"), command=self._clear_form,
        )
        for button in (
            self._add_btn, self._update_btn, self._delete_btn,
            self._maint_btn, self._finish_btn, self._clear_btn,
        ):
            button.pack(side="left", padx=(0, 8))

        self._status = ctk.CTkLabel(form, text="", anchor="w")
        self._status.pack(fill="x", padx=14, pady=(2, 10))

    @staticmethod
    def _menu_field(
        parent: ctk.CTkFrame, label: str, values: list[str], column: int
    ) -> ctk.CTkOptionMenu:
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=0, column=column, padx=6, sticky="w")
        ctk.CTkLabel(box, text=label, anchor="w").pack(fill="x")
        menu = ctk.CTkOptionMenu(box, values=values, width=150)
        menu.pack(fill="x")
        return menu

    # ------------------------------------------------------------------
# Display Data
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        branches = self._car_rental.branches
        labels = [f"{b.branch_id} - {b.name}" for b in branches] or ["(no branches)"]
        current = self._branch_menu.get()
        self._branch_menu.configure(values=labels)
        self._branch_menu.set(current if current in labels else labels[0])
        self._reload_table()

    def _reload_table(self) -> None:
        status = self._bar.filter_value("Status")
        type_name = self._bar.filter_value("Type")
        vehicles = self._car_rental.filter_vehicles(
            status=None if status == "All" else status,
            type_name=None if type_name == "All" else type_name,
        )
        text = self._bar.search_text
        if text:
            matched = {v.plate for v in self._car_rental.search_vehicles(text)}
            vehicles = [v for v in vehicles if v.plate in matched]

        branch_names = {b.branch_id: b.name for b in self._car_rental.branches}
        rows = [
            (
                v.plate,
                (
                    v.plate,
                    v.brand,
                    v.model,
                    v.type_name,
                    f"{v.base_rate:,.2f}",
                    f"{v.calculate_daily_rate():,.2f}",   # Polymorphism: كل نوع بسعره
                    f"{v.calculate_insurance():,.2f}",
                    v.status,
                    branch_names.get(v.branch_id, v.branch_id),
                ),
            )
            for v in vehicles
        ]
        self._table.set_rows(rows)

    # ------------------------------------------------------------------
    # أوضاع الفورم: إضافة (مفيش صف مختار) / تعديل (فيه صف مختار)
    # ------------------------------------------------------------------
    def _set_mode(self, plate: str | None) -> None:
        editing = plate is not None
        for entry in (self._plate, self._brand, self._model):
            entry.set_enabled(not editing)   # اللوحة والماركة والموديل مبتتغيرش
        self._type_menu.configure(state="disabled" if editing else "normal")
        self._add_btn.configure(state="disabled" if editing else "normal")
        for button in (self._update_btn, self._delete_btn, self._maint_btn, self._finish_btn):
            button.configure(state="normal" if editing else "disabled")

    def _on_row_select(self, plate: str | None) -> None:
        if plate is None:
            self._selected = None
            self._set_mode(None)
            return
        try:
            vehicle = self._car_rental.get_vehicle(plate)
        except ValueError:
            return
        self._selected = plate
        self._plate.set(vehicle.plate)
        self._brand.set(vehicle.brand)
        self._model.set(vehicle.model)
        self._rate.set(f"{vehicle.base_rate:g}")
        self._type_menu.set(vehicle.type_name)
        for branch in self._car_rental.branches:
            if branch.branch_id == vehicle.branch_id:
                self._branch_menu.set(f"{branch.branch_id} - {branch.name}")
        self._set_mode(plate)
        self._set_status("")

    def _clear_form(self) -> None:
        self._table.clear_selection()
        self._selected = None
        self._set_mode(None)
        for entry in (self._plate, self._brand, self._model, self._rate):
            entry.clear()
        self._set_status("")

    # ------------------------------------------------------------------
    #   Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_rate(text: str) -> float:
        try:
            return float(text.replace(",", ""))
        except ValueError:
            raise ValueError("السعر يجب أن يكون رقماً") from None

    def _branch_id(self) -> str:
        return self._branch_menu.get().split(" - ")[0]

    def _need_selection(self) -> str:
        if self._selected is None:
            raise ValueError("اختر سيارة من الجدول أولاً")
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

    # ------------------------------------------------------------------
    # الأزرار
    # ------------------------------------------------------------------
    def _on_add(self) -> None:
        try:
            vehicle = self._car_rental.add_vehicle(
                self._type_menu.get(),
                self._plate.get(),
                self._brand.get(),
                self._model.get(),
                self._parse_rate(self._rate.get()),
                self._branch_id(),
            )
        except ValueError as e:
            self._fail(e)
            return
        self._done(f"Added {vehicle.plate}")

    def _on_update(self) -> None:
        try:
            plate = self._need_selection()
            self._car_rental.update_vehicle(
                plate,
                base_rate=self._parse_rate(self._rate.get()),
                branch_id=self._branch_id(),
            )
        except ValueError as e:
            self._fail(e)
            return
        self._done(f"Updated {plate}")

    def _on_delete(self) -> None:
        try:
            plate = self._need_selection()
            if not self.confirm(f"Delete vehicle {plate}?"):
                return
            self._car_rental.delete_vehicle(plate)
        except ValueError as e:
            self._fail(e)
            return
        self._done(f"Deleted {plate}")

    def _on_maintenance(self) -> None:
        try:
            plate = self._need_selection()
            self._car_rental.send_to_maintenance(plate)
        except ValueError as e:
            self._fail(e)
            return
        self._done(f"{plate} sent to maintenance")

    def _on_finish_maintenance(self) -> None:
        try:
            plate = self._need_selection()
            self._car_rental.finish_maintenance(plate)
        except ValueError as e:
            self._fail(e)
            return
        self._done(f"{plate} is available again")