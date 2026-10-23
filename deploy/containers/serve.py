"""Container-only entry point; the operator owns TLS/ingress, not this image."""

import os
import uvicorn
from musia.creator.api import create_app

os.umask(0o077)
uvicorn.run(create_app(), host="0.0.0.0", port=8796, access_log=False,
            proxy_headers=False, workers=1, limit_concurrency=32,
            timeout_keep_alive=5, timeout_graceful_shutdown=100)
