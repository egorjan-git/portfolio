from __future__ import annotations

from typing import List, Optional, Dict
from pathlib import Path

from hash_collection import HashCollection
from models import CarBase, CarType


class CarCatalog:
    def __init__(self, other: Optional["CarCatalog"] = None) -> None:
        self._cars: HashCollection[int, CarBase] = HashCollection()
        if other is not None:
            for car in other.list_all():
                self.add(car.copy())

    def __del__(self) -> None:
        self.clear()

    def copy(self) -> "CarCatalog":
        return CarCatalog(self)

    def add(self, car: CarBase) -> None:
        if not isinstance(car, CarBase):
            raise ValueError("car must be CarBase")
        self._cars.add(car.id, car)

    def __lshift__(self, car: CarBase) -> "CarCatalog":
        # catalog << car
        self.add(car)
        return self

    def remove(self, car_id: int) -> bool:
        return self._cars.remove(car_id)

    def clear(self) -> None:
        self._cars.clear()

    def count(self) -> int:
        return len(self._cars)

    def contains_id(self, car_id: int) -> bool:
        return self._cars.contains(car_id)

    def __contains__(self, car_id: int) -> bool:
        return self.contains_id(car_id)

    def __getitem__(self, car_id: int) -> CarBase:
        return self._cars[car_id]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CarCatalog):
            return False
        return self._cars == other._cars

    def __and__(self, other: "CarCatalog") -> "CarCatalog":
        out = CarCatalog()
        inter = self._cars & other._cars
        for _, car in inter.items():
            out.add(car.copy())
        return out

    def list_all(self) -> List[CarBase]:
        return list(self._cars.values())

    def group_by_type(self) -> Dict[str, List[CarBase]]:
        groups: Dict[str, List[CarBase]] = {}
        for car in self._cars.values():
            t = car.car_type.value
            if t not in groups:
                groups[t] = []
            groups[t].append(car)
        for t in groups:
            groups[t].sort()
        return groups

    def save(self, path: str | Path) -> None:
        p = Path(path)
        self._cars.save(p, serializer=lambda c: c.to_dict())

    def load(self, path: str | Path) -> None:
        p = Path(path)
        if not p.exists():
            self.clear()
            return
        self._cars.load(p, deserializer=lambda d: CarBase.from_dict(d))
