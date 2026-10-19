from __future__ import annotations

from abc import ABC, abstractmethod
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from Services.car_rentel import CarRental


class BasePage(ctk.CTkFrame, ABC):
   

    TITLE: str = "Page"

    def __init__(
        self,
        parent: ctk.CTkFrame,
        car_rental: CarRental,
        navigate: Callable[[str], None],
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        self._car_rental: CarRental = car_rental
        self._navigate: Callable[[str], None] = navigate  

        self._title_label = ctk.CTkLabel(
            self, text=self.TITLE, font=ctk.CTkFont(size=24, weight="bold")
        )
        self._title_label.pack(anchor="w", padx=24, pady=(20, 8))


    @abstractmethod
    def refresh(self) -> None:
        """يحدّث محتوى الصفحة من بيانات CarRental."""

    # ---------- رسائل المستخدم (مشتركة بين كل الصفحات) ----------

    def show_error(self, error: Exception | str) -> None:
        messagebox.showerror("Error", str(error))

    def show_info(self, message: str) -> None:
        messagebox.showinfo("Done", message)

    def confirm(self, message: str) -> bool:
        return messagebox.askyesno("Confirm", message)


class PlaceholderPage(BasePage):

    TITLE: str = "Coming soon"

    def __init__(
        self,
        parent: ctk.CTkFrame,
        car_rental: CarRental,
        navigate: Callable[[str], None],
    ) -> None:
        super().__init__(parent, car_rental, navigate)
        ctk.CTkLabel(self, text="This page is not built yet.").pack(
            anchor="w", padx=24, pady=8
        )

    def refresh(self) -> None:
        pass  