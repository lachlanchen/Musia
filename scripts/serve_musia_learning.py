#!/usr/bin/env python3
"""Run only the public, read-only Musia learning service."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from musia.learning import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18440)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    try:
        app = create_app()
    except ValueError as error:
        parser.error(str(error))
    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, proxy_headers=False,
                server_header=False, access_log=False, limit_concurrency=32,
                timeout_keep_alive=5, h11_max_incomplete_event_size=16384)


if __name__ == "__main__":
    main()
