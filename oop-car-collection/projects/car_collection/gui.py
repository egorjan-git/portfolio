from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from pathlib import Path

from catalog import CarCatalog
from io_table import export_csv, import_csv
from models import CarType, SportsCar, Truck, ClassicCar, SuvCar, OtherCar, CarBase


def _make_car_from_form(values: dict) -> CarBase:
    car_id = int(values["id"])
    car_type = CarType(values["type"])
    cls_map = {
        CarType.SPORT: SportsCar,
        CarType.TRUCK: Truck,
        CarType.CLASSIC: ClassicCar,
        CarType.SUV: SuvCar,
        CarType.OTHER: OtherCar,
    }
    cls = cls_map.get(car_type, OtherCar)
    price_raw = values.get("price", "").strip()
    price = None if price_raw == "" else float(price_raw)
    return cls(
        car_id=car_id,
        brand=values["brand"],
        model=values["model"],
        year=int(values["year"]),
        scale=values["scale"],
        condition=values["condition"],
        price=price,
        notes=values.get("notes", ""),
    )


class CatalogGUI(tk.Tk):
    def __init__(self, catalog: CarCatalog, data_path: Path) -> None:
        super().__init__()
        self.title("Car Catalog")
        self.geometry("980x520")

        self._catalog = catalog
        self._data_path = data_path

        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)

        ttk.Button(top, text="Add", command=self._add_dialog).pack(side="left")
        ttk.Button(top, text="Edit", command=self._edit_selected).pack(side="left", padx=6)
        ttk.Button(top, text="Remove", command=self._remove_selected).pack(side="left")
        ttk.Button(top, text="Save", command=self._save).pack(side="left", padx=20)
        ttk.Button(top, text="Load", command=self._load).pack(side="left")
        ttk.Button(top, text="Import CSV", command=self._import_csv).pack(side="left", padx=20)
        ttk.Button(top, text="Export CSV", command=self._export_csv).pack(side="left")

        ttk.Label(top, text="Filter type:").pack(side="left", padx=20)
        self._filter = tk.StringVar(value="all")
        self._filter_box = ttk.Combobox(
            top,
            textvariable=self._filter,
            values=["all"] + [t.value for t in CarType],
            state="readonly",
            width=10,
        )
        self._filter_box.pack(side="left")
        self._filter_box.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        cols = ("id", "brand", "model", "year", "scale", "type", "condition", "price")
        self._tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self._tree.heading(c, text=c)
            self._tree.column(c, width=110 if c != "model" else 180, anchor="center")
        self._tree.pack(fill="both", expand=True, padx=8, pady=8)

    def _refresh(self) -> None:
        for x in self._tree.get_children():
            self._tree.delete(x)

        cars = self._catalog.list_all()
        cars.sort()
        f = self._filter.get()
        for car in cars:
            if f != "all" and car.car_type.value != f:
                continue
            price = "" if car.price is None else f"{car.price:.2f}"
            self._tree.insert(
                "",
                "end",
                values=(car.id, car.brand, car.model, car.year, car.scale, car.car_type.value, car.condition, price),
            )

    def _selected_id(self):
        sel = self._tree.selection()
        if not sel:
            return None
        vals = self._tree.item(sel[0], "values")
        return int(vals[0])

    def _save(self) -> None:
        try:
            self._catalog.save(self._data_path)
            messagebox.showinfo("OK", "Saved")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _load(self) -> None:
        try:
            self._catalog.load(self._data_path)
            self._refresh()
            messagebox.showinfo("OK", "Loaded")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _import_csv(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            cars = import_csv(path)
            for c in cars:
                self._catalog.add(c)
            self._refresh()
            messagebox.showinfo("OK", f"Imported {len(cars)} rows")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            export_csv(path, self._catalog.list_all())
            messagebox.showinfo("OK", "Exported")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _remove_selected(self) -> None:
        cid = self._selected_id()
        if cid is None:
            return
        if not messagebox.askyesno("Confirm", f"Remove id={cid}?"):
            return
        self._catalog.remove(cid)
        self._refresh()

    def _edit_selected(self) -> None:
        cid = self._selected_id()
        if cid is None:
            return
        car = self._catalog[cid]
        self._car_dialog(title=f"Edit id={cid}", initial=car.to_dict(), on_ok=lambda d: self._apply_edit(cid, d))

    def _apply_edit(self, cid: int, d: dict) -> None:
        car = self._catalog[cid]
        car.brand = d["brand"]
        car.model = d["model"]
        car.year = int(d["year"])
        car.scale = d["scale"]
        car.condition = d["condition"]
        pr = d.get("price", "").strip()
        car.price = None if pr == "" else float(pr)
        car.notes = d.get("notes", "")
        new_type = CarType(d["type"])
        if new_type != car.car_type:
            new_car = _make_car_from_form(d)
            self._catalog.add(new_car)
        self._refresh()

    def _add_dialog(self) -> None:
        self._car_dialog(title="Add car", initial=None, on_ok=self._add_from_dict)

    def _add_from_dict(self, d: dict) -> None:
        car = _make_car_from_form(d)
        self._catalog.add(car)
        self._refresh()

    def _car_dialog(self, title: str, initial, on_ok) -> None:
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.grab_set()

        fields = ["id", "brand", "model", "year", "scale", "type", "condition", "price", "notes"]
        vars = {f: tk.StringVar(value="" if initial is None else str(initial.get(f, ""))) for f in fields}
        if initial is not None and "type" in initial:
            vars["type"].set(str(initial["type"]))

        frm = ttk.Frame(dlg)
        frm.pack(padx=10, pady=10, fill="both", expand=True)

        for i, f in enumerate(fields):
            ttk.Label(frm, text=f).grid(row=i, column=0, sticky="w", pady=3)
            if f == "type":
                cb = ttk.Combobox(frm, textvariable=vars[f], values=[t.value for t in CarType], state="readonly")
                cb.grid(row=i, column=1, sticky="ew", pady=3)
            else:
                ttk.Entry(frm, textvariable=vars[f]).grid(row=i, column=1, sticky="ew", pady=3)

        frm.columnconfigure(1, weight=1)

        def ok():
            data = {f: vars[f].get() for f in fields}
            try:
                on_ok(data)
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btns = ttk.Frame(dlg)
        btns.pack(fill="x", padx=10, pady=10)
        ttk.Button(btns, text="OK", command=ok).pack(side="right")
        ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="right", padx=6)


def run_gui(catalog: CarCatalog, data_path: Path) -> None:
    app = CatalogGUI(catalog, data_path)
    app.protocol("WM_DELETE_WINDOW", lambda: (catalog.save(data_path), app.destroy()))
    app.mainloop()
