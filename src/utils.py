"""
Utility helpers.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: str | Path, indent: int = 2) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def pretty_print_entities(entities: List[Dict]) -> None:
    if not entities:
        print("No entities found.")
        return
    print(f"{'Type':<18} {'Text':<30} {'Score':<8} {'Risk':<10} Source")
    print("-" * 80)
    for e in entities:
        print(
            f"{e['entity_type']:<18} {e['text'][:28]:<30} "
            f"{e['score']:<8.2f} {e['risk']:<10} {e.get('source', '')}"
        )
