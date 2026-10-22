"""Start the API on a platform-provided port without changing local defaults."""

from __future__ import annotations

import os
import sys


def main() -> int:
    """Replace this process with Uvicorn using a validated HTTP port."""
    raw_port = os.environ.get("PORT", "8000")
    try:
        port = int(raw_port)
    except ValueError:
        print("PORT must be an integer.", file=sys.stderr)
        return 2

    if not 1 <= port <= 65535:
        print("PORT must be between 1 and 65535.", file=sys.stderr)
        return 2

    os.execvp(
        "uvicorn",
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(port)],
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
