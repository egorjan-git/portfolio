from __future__ import annotations

from pathlib import Path
import tempfile
import os

from hash_collection import HashCollection
from models import SportsCar, Truck, CarBase
from catalog import CarCatalog
from io_table import export_csv, import_csv


def test_hash_collection_basic():
    c = HashCollection[int, str]()
    assert len(c) == 0
    c.add(1, "a")
    c.add(2, "b")
    assert c.count() == 2
    assert c.contains(1) is True
    assert c[2] == "b"

    c << (3, "c")
    assert c[3] == "c"
    assert 3 in c

    assert c.remove(2) is True
    assert c.remove(2) is False
    assert len(c) == 2

    c2 = c.copy()
    assert c2 == c
    c2.add(99, "x")
    assert c2 != c

    inter = c & c2
    assert inter == c

    c.clear()
    assert len(c) == 0


def test_car_validation_and_copy():
    car = SportsCar(car_id=1, brand="Hot Wheels", model="GT", year=2020, scale="1:64", condition="new", price=10)
    assert car.id == 1
    assert car.brand == "Hot Wheels"
    assert "sport" in car.to_dict()["type"]

    car2 = car.copy()
    assert car2 == car
    assert car2 is not car

    try:
        SportsCar(car_id=0, brand="x", model="y", year=2020, scale="1:64")
        assert False
    except ValueError:
        pass

    try:
        SportsCar(car_id=1, brand="", model="y", year=2020, scale="1:64")
        assert False
    except ValueError:
        pass


def test_catalog_group_save_load():
    cat = CarCatalog()
    cat.add(SportsCar(1, "A", "M1", 2010, "1:64", "ok", 1.0, ""))
    cat.add(Truck(2, "B", "T1", 2005, "1:43", "ok", None, ""))

    groups = cat.group_by_type()
    assert "sport" in groups
    assert "truck" in groups
    assert cat.count() == 2
    assert cat.contains_id(1)

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "data.json"
        cat.save(p)
        cat2 = CarCatalog()
        cat2.load(p)
        assert cat2.count() == 2
        assert cat2[1].brand == "A"


def test_csv_import_export():
    cat = CarCatalog()
    cat.add(SportsCar(1, "A", "M1", 2010, "1:64", "ok", 1.0, "n"))
    cat.add(Truck(2, "B", "T1", 2005, "1:43", "ok", None, ""))

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "out.csv"
        export_csv(p, cat.list_all())
        cars = import_csv(p)
        assert len(cars) == 2
        assert any(c.id == 1 for c in cars)


def run_all_tests():
    test_hash_collection_basic()
    test_car_validation_and_copy()
    test_catalog_group_save_load()
    test_csv_import_export()
    print("All tests passed")


if __name__ == "__main__":
    run_all_tests()
