from datetime import datetime
from pathlib import Path
from typing import Final, Protocol


class StoragePathProvider(Protocol):
    def get_target_dir(self) -> Path: ...


MONTH_MAP: Final[dict[int, str]] = {
    1: "styczen",
    2: "luty",
    3: "marzec",
    4: "kwiecien",
    5: "maj",
    6: "czerwiec",
    7: "lipiec",
    8: "sierpien",
    9: "wrzesien",
    10: "pazdziernik",
    11: "listopad",
    12: "grudzien",
}


class DateBasedPathProvider:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def get_target_dir(self) -> Path:
        current_month = datetime.now().month
        month_name = MONTH_MAP[current_month]
        target_path = self._base_dir / month_name

        target_path.mkdir(parents=True, exist_ok=True)
        return target_path
