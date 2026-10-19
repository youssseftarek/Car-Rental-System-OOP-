from __future__ import annotations

from tkinter import ttk
from typing import Any, Callable, Sequence

import customtkinter as ctk

_style_ready: bool = False


def _configure_tree_style() -> None:
    global _style_ready
    if _style_ready:
        return
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Treeview",
        background="#ffffff",
        fieldbackground="#ffffff",
        foreground="#1a1a1a",
        rowheight=30,
        borderwidth=0,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Treeview.Heading",
        background="#e8edf3",
        foreground="#1a1a1a",
        font=("Segoe UI", 10, "bold"),
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", "#3B8ED0")],
        foreground=[("selected", "white")],
    )
    style.map("Treeview.Heading", background=[("active", "#d5dde8")])
    _style_ready = True


class StatCard(ctk.CTkFrame):

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        title: str,
        value: str = "0",
        accent: str = "#3B8ED0",
    ) -> None:
        super().__init__(
            parent, corner_radius=8, border_width=1, border_color=("gray80", "gray30")
        )
        ctk.CTkFrame(self, height=4, corner_radius=2, fg_color=accent).pack(
            fill="x", padx=14, pady=(12, 0)
        )
        self._value_label = ctk.CTkLabel(
            self, text=value, font=ctk.CTkFont(size=26, weight="bold")
        )
        self._value_label.pack(anchor="w", padx=14, pady=(8, 0))
        ctk.CTkLabel(self, text=title, text_color="gray45").pack(
            anchor="w", padx=14, pady=(0, 12)
        )

    def set_value(self, value: str) -> None:
        self._value_label.configure(text=value)


class DataTable(ctk.CTkFrame):

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        columns: Sequence[tuple[str, str, int]],  # (المفتاح، العنوان، العرض)
        height: int = 10,
        empty_text: str = "No data",
        on_select: Callable[[str | None], None] | None = None,
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        _configure_tree_style()
        self._on_select = on_select

        keys = [key for key, _heading, _width in columns]
        self._tree = ttk.Treeview(
            self, columns=keys, show="headings", height=height, selectmode="browse"
        )
        for key, heading, width in columns:
            self._tree.heading(key, text=heading)
            self._tree.column(key, width=width, anchor="w")

        scrollbar = ctk.CTkScrollbar(self, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # رسالة بتظهر فوق الجدول لما يكون فاضي
        self._empty_label = ctk.CTkLabel(
            self, text=empty_text, text_color="gray50", fg_color="white"
        )
        self._tree.bind("<<TreeviewSelect>>", self._handle_select)

    def set_rows(self, rows: Sequence[tuple[str, Sequence[Any]]]) -> None:

        self._tree.delete(*self._tree.get_children())
        for row_id, values in rows:
            self._tree.insert("", "end", iid=row_id, values=[str(v) for v in values])
        if rows:
            self._empty_label.place_forget()
        else:
            self._empty_label.place(relx=0.5, rely=0.5, anchor="center")

    def selected_id(self) -> str | None:
        selection = self._tree.selection()
        return selection[0] if selection else None

    def clear_selection(self) -> None:
        self._tree.selection_remove(*self._tree.selection())
    def select(self, row_id: str) -> None:
        
        if self._tree.exists(row_id):
            self._tree.selection_set(row_id)
            self._tree.see(row_id)
    def _handle_select(self, _event: object) -> None:
        if self._on_select is not None:
            self._on_select(self.selected_id())


class SearchFilterBar(ctk.CTkFrame):

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        on_change: Callable[[], None],
        placeholder: str = "Search...",
        filters: dict[str, list[str]] | None = None,
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        self._on_change = on_change

        self._entry = ctk.CTkEntry(self, placeholder_text=placeholder, width=260)
        self._entry.pack(side="left", padx=(0, 12))
        self._entry.bind("<KeyRelease>", lambda _e: self._on_change())

        self._menus: dict[str, ctk.CTkOptionMenu] = {}
        for label, options in (filters or {}).items():
            ctk.CTkLabel(self, text=label).pack(side="left", padx=(0, 4))
            menu = ctk.CTkOptionMenu(
                self,
                values=options,  # أول اختيار = "الكل"
                width=130,
                command=lambda _value: self._on_change(),
            )
            menu.pack(side="left", padx=(0, 12))
            self._menus[label] = menu

    @property
    def search_text(self) -> str:
        return self._entry.get().strip()

    def filter_value(self, label: str) -> str:
        return self._menus[label].get()

    def reset(self) -> None:
        self._entry.delete(0, "end")
        for menu in self._menus.values():
            menu.set(menu.cget("values")[0])


class LabeledEntry(ctk.CTkFrame):
   

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        label: str,
        placeholder: str = "",
        width: int = 220,
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text=label, anchor="w").pack(fill="x")
        self._entry = ctk.CTkEntry(self, placeholder_text=placeholder, width=width)
        self._entry.pack(fill="x")

    def get(self) -> str:
        return self._entry.get().strip()

    def set(self, value: str) -> None:
       
        state = self._entry.cget("state")
        self._entry.configure(state="normal")
        self._entry.delete(0, "end")
        self._entry.insert(0, value)
        self._entry.configure(state=state)

    def clear(self) -> None:
        self.set("")

    def set_enabled(self, enabled: bool) -> None:
        self._entry.configure(state="normal" if enabled else "disabled")