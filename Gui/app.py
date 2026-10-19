
from __future__ import annotations

import importlib
from tkinter import messagebox

import customtkinter as ctk

from Gui.pages.base_page import BasePage, PlaceholderPage
from Services.car_rentel import CarRental


class App(ctk.CTk):
 
    NAV_ITEMS: list[tuple[str, str]] = [
        ("dashboard", "Dashboard"),
        ("vehicles", "Vehicles"),
        ("customers", "Customers"),
        ("rentals", "Rentals"),
        ("payments", "Payments"),
    ]

   
    PAGE_MODULES: dict[str, tuple[str, str]] = {
        "dashboard": ("Gui.pages.dashboard_page", "DashboardPage"),
        "vehicles": ("Gui.pages.vehicles_page", "VehiclesPage"),
        "customers": ("Gui.pages.customers_page", "CustomersPage"),
        "rentals": ("Gui.pages.rentals_page", "RentalsPage"),
        "payments": ("Gui.pages.payments_page", "PaymentsPage"),
    }

    ACTIVE_COLOR: tuple[str, str] = ("#3B8ED0", "#1F6AA5")

    def __init__(self, car_rental: CarRental) -> None:
        super().__init__()
        self._car_rental: CarRental = car_rental  

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("Car Rental Management System")
        self.geometry("1200x720")
        self.minsize(1000, 600)

        self.grid_columnconfigure(1, weight=1)  
        self.grid_rowconfigure(0, weight=1)

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._pages: dict[str, BasePage] = {}
        self._current: str | None = None

        self._build_sidebar()
        self._build_pages()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.show_page("dashboard")

    # ---------- بناء الواجهة ----------
    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar, text="Car Rental", font=ctk.CTkFont(size=22, weight="bold")
        ).pack(padx=20, pady=(28, 24))

        for key, label in self.NAV_ITEMS:
            button = ctk.CTkButton(
                sidebar,
                text=label,
                anchor="w",
                height=40,
                corner_radius=6,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray75", "gray30"),
                command=lambda k=key: self.show_page(k),
            )
            button.pack(fill="x", padx=12, pady=3)
            self._nav_buttons[key] = button

    @staticmethod
    def _load_page_class(module_name: str, class_name: str) -> type[BasePage]:
      
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as e:
            if e.name == module_name:  
                return PlaceholderPage
            raise 
        return getattr(module, class_name)

    def _build_pages(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=1, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        for key, (module_name, class_name) in self.PAGE_MODULES.items():
            page_class = self._load_page_class(module_name, class_name)
            page = page_class(container, self._car_rental, self.show_page)
            page.grid(row=0, column=0, sticky="nsew")  
            self._pages[key] = page

    # ---------- التنقل ----------
    def show_page(self, key: str) -> None:
       
        if key not in self._pages:
            raise ValueError(f"الصفحة {key} غير موجودة")
        page = self._pages[key]
        page.refresh()  
        page.tkraise()  
        self._current = key
        self._highlight(key)

    def _highlight(self, active_key: str) -> None:
        for key, button in self._nav_buttons.items():
            if key == active_key:
                button.configure(fg_color=self.ACTIVE_COLOR, text_color="white")
            else:
                button.configure(
                    fg_color="transparent", text_color=("gray10", "gray90")
                )

    # ---------- الإغلاق ----------
    def _on_close(self) -> None:
       
        try:
            self._car_rental.save()
        except ValueError as e:
            if not messagebox.askyesno("Save failed", f"{e}\n\nExit anyway?"):
                return
        self.destroy()