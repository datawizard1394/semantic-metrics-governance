from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


def catalog_dict() -> dict[str, Any]:
    return json.loads(Path("examples/catalog.json").read_text(encoding="utf-8"))


def cloned_catalog_dict() -> dict[str, Any]:
    return copy.deepcopy(catalog_dict())

