#!/usr/bin/env python3
"""Index Medical_KB markdown into Qdrant (Phase 2.3).

Run from repo root:

  python scripts/index_kb.py

This runs the backend indexer (requires backend deps and Qdrant). Alternatively:

  cd backend && uv run python -c "from app.services.rag import index_kb; print(index_kb())"
"""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    backend = repo_root / "backend"
    if not backend.is_dir():
        print("backend/ not found", file=sys.stderr)
        return 1
    # Use uv run so backend venv and deps are used
    cmd = [
        "uv",
        "run",
        "python",
        "-c",
        "from app.services.rag import index_kb; print(index_kb())",
    ]
    result = subprocess.run(cmd, cwd=str(backend), capture_output=False)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
