from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List

from models import CarBase


CSV_FIELDS = ["id", "brand", "model", "year", "scale", "condition", "price", "notes", "type"]


def export_csv(path: str | Path, cars: Iterable[CarBase]) -> None:
    p = Path(path)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for car in cars:
            d = car.to_dict()
            w.writerow(d)


def import_csv(path: str | Path) -> List[CarBase]:
    p = Path(path)
    out: List[CarBase] = []
    with p.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        if r.fieldnames is None:
            raise ValueError("Empty CSV")
        for row in r:
            # normalize types
            d = dict(row)
            d["id"] = int(d["id"])
            d["year"] = int(d["year"])
            pr = d.get("price", "")
            if pr is None or str(pr).strip() == "":
                d["price"] = None
            else:
                d["price"] = float(pr)
            out.append(CarBase.from_dict(d))
    return out
