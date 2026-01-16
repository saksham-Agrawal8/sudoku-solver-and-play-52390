"""
Generate and export the FastAPI OpenAPI schema to the repository interfaces folder.

This script is intended to be run from the backend container root:

    python src/api/generate_openapi.py

It writes:
    sudoku_backend/interfaces/openapi.json
"""

import json
import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    """
    Ensure the backend container root is on sys.path so `import src.*` works
    when executing this script directly.
    """
    backend_root = Path(__file__).resolve().parents[2]  # .../sudoku_backend
    sys.path.insert(0, str(backend_root))


def main() -> None:
    """Generate the OpenAPI schema and write it to interfaces/openapi.json."""
    _ensure_src_on_path()

    from src.api.main import app  # noqa: WPS433 (local import needed after sys.path fix)

    openapi_schema = app.openapi()

    backend_root = Path(__file__).resolve().parents[2]  # .../sudoku_backend
    output_dir = backend_root / "interfaces"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "openapi.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
