from __future__ import annotations

from typing import Optional
from pathlib import Path

from catalog import CarCatalog
from io_table import export_csv, import_csv
from models import SportsCar, Truck, ClassicCar, SuvCar, OtherCar, CarBase, CarType


def _read_int(prompt: str) -> int:
    s = input(prompt).strip()
    return int(s)


def _read_float_optional(prompt: str):
    s = input(prompt).strip()
    if s == "":
        return None
    return float(s)


def _read_str(prompt: str) -> str:
    return input(prompt).strip()


def _choose_type() -> CarType:
    print("Type:", ", ".join([t.value for t in CarType]))
    s = input("type> ").strip().lower()
    try:
        return CarType(s)
    except Exception:
        return CarType.OTHER


def _make_car(
    car_id: int,
    car_type: CarType,
    brand: str,
    model: str,
    year: int,
    scale: str,
    condition: str,
    price,
    notes: str,
) -> CarBase:
    cls_map = {
        CarType.SPORT: SportsCar,
        CarType.TRUCK: Truck,
        CarType.CLASSIC: ClassicCar,
        CarType.SUV: SuvCar,
        CarType.OTHER: OtherCar,
    }
    cls = cls_map.get(car_type, OtherCar)
    return cls(
        car_id=car_id,
        brand=brand,
        model=model,
        year=year,
        scale=scale,
        condition=condition,
        price=price,
        notes=notes,
    )


def run_cli(catalog: CarCatalog, data_path: Path) -> None:
    while True:
        print("\n=== Car Catalog CLI ===")
        print("1) List all")
        print("2) Group by type")
        print("3) Add")
        print("4) Remove")
        print("5) Modify")
        print("6) Import CSV")
        print("7) Export CSV")
        print("8) Save")
        print("9) Load")
        print("0) Exit")
        cmd = input("> ").strip()

        try:
            if cmd == "1":
                cars = catalog.list_all()
                cars.sort()
                for c in cars:
                    print(str(c))
                print(f"Total: {catalog.count()}")

            elif cmd == "2":
                groups = catalog.group_by_type()
                for t, items in groups.items():
                    print(f"\n[{t}] ({len(items)})")
                    for c in items:
                        print(" ", str(c))

            elif cmd == "3":
                car_id = _read_int("id> ")
                car_type = _choose_type()
                brand = _read_str("brand> ")
                model = _read_str("model> ")
                year = _read_int("year> ")
                scale = _read_str("scale (e.g. 1:64)> ")
                condition = _read_str("condition> ")
                price = _read_float_optional("price (empty=none)> ")
                notes = _read_str("notes> ")
                catalog.add(_make_car(car_id, car_type, brand, model, year, scale, condition, price, notes))
                print("OK")

            elif cmd == "4":
                car_id = _read_int("id> ")
                ok = catalog.remove(car_id)
                print("Removed" if ok else "Not found")

            elif cmd == "5":
                car_id = _read_int("id> ")
                car = catalog[car_id]
                print("Current:", str(car))
                print("Leave empty to keep field.")
                brand = _read_str("brand> ")
                model = _read_str("model> ")
                year_s = _read_str("year> ")
                scale = _read_str("scale> ")
                condition = _read_str("condition> ")
                price_s = _read_str("price> ")
                notes = _read_str("notes> ")

                if brand:
                    car.brand = brand
                if model:
                    car.model = model
                if year_s:
                    car.year = int(year_s)
                if scale:
                    car.scale = scale
                if condition:
                    car.condition = condition
                if price_s:
                    car.price = float(price_s)
                if notes:
                    car.notes = notes
                print("OK")

            elif cmd == "6":
                path = Path(_read_str("csv path> "))
                cars = import_csv(path)
                for c in cars:
                    catalog.add(c)
                print(f"Imported: {len(cars)}")

            elif cmd == "7":
                path = Path(_read_str("csv path> "))
                export_csv(path, catalog.list_all())
                print("Exported")

            elif cmd == "8":
                catalog.save(data_path)
                print("Saved")

            elif cmd == "9":
                catalog.load(data_path)
                print("Loaded")

            elif cmd == "0":
                catalog.save(data_path)
                print("Saved. Bye.")
                return

            else:
                print("Unknown command")

        except Exception as e:
            print("Error:", e)
