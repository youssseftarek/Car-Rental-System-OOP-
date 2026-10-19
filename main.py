
from __future__ import annotations

from pathlib import Path
from tkinter import Tk, messagebox

from File_Manger.File_manger import FileManager
from Gui.app import App
from Services.car_rentel import CarRental


DATA_DIR: Path = Path(__file__).resolve().parent / "data"


def build_car_rental() -> CarRental:
   
    car_rental = CarRental(FileManager(DATA_DIR))
    car_rental.load()
    if not car_rental.branches:  
        car_rental.add_branch("Main Branch", "Cairo")
    return car_rental


def main() -> None:
    try:
        car_rental = build_car_rental()
    except ValueError as e:
      
        root = Tk()
        root.withdraw()
        messagebox.showerror("Cannot start", str(e))
        root.destroy()
        return

    App(car_rental).mainloop()


if __name__ == "__main__":
    main()