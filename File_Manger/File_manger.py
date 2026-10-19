
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, Sequence


class FileManager:

    def __init__(self, data_dir: str | Path = "data") -> None:
        self._data_dir: Path = Path(data_dir)

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    # ---------- JSON ----------
    def read_json(self, filename: str) -> list[dict[str, Any]]:
         
        path = self._data_dir / filename
        if not path.exists():
            return []
        try:
            text = path.read_text(encoding="utf-8")
            if not text.strip():
                return []
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"الملف {filename} تالف ولا يمكن قراءته") from e
        except OSError as e:
            raise ValueError(f"تعذر فتح الملف {filename}: {e}") from e

        if not isinstance(data, list):
            raise ValueError(f"محتوى الملف {filename} غير صحيح (المتوقع قائمة)")
        return data

    # ---------- JSON ----------
    def write_json(self, filename: str, data: list[dict[str, Any]]) -> None:

        path = self._data_dir / filename
        temp_path = path.with_name(path.name + ".tmp")
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            temp_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(temp_path, path)  
        except (OSError, TypeError) as e:
            temp_path.unlink(missing_ok=True) 
            raise ValueError(f"تعذر حفظ الملف {filename}: {e}") from e

    # ---------- CSV ----------
    def export_csv(
        self,
        file_path: str | Path,
        headers: Sequence[str],
        rows: Sequence[Sequence[Any]],
    ) -> None:
     
        if not headers:
            raise ValueError("عناوين الأعمدة مطلوبة")
        path = Path(file_path)
        try:
       
            with path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
        except OSError as e:
            raise ValueError(f"تعذر حفظ ملف التقرير: {e}") from e