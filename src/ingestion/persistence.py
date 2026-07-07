import json
from pathlib import Path
from typing import Any

def save_json(data: dict[str, Any], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
            default=str,
            allow_nan=False,
        )