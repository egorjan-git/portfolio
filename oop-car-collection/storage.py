from __future__ import annotations

from pathlib import Path
from catalog import CarCatalog

DEFAULT_DATA_FILE = "data.json"


class Storage:
    def __init__(self, data_file: str = DEFAULT_DATA_FILE) -> None:
        self._path = Path(data_file)

    @property
    def path(self) -> Path:
        return self._path

    def load_catalog(self) -> CarCatalog:
        cat = CarCatalog()
        cat.load(self._path)
        return cat

    def save_catalog(self, catalog: CarCatalog) -> None:
        catalog.save(self._path)
