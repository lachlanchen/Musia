"""App-side transport boundary. Native sessions remain owned by creator.api."""
import hmac
import ipaddress
import os
from pathlib import Path
import re
import stat

CLIENT_AUTH = b"x-musia-client-authorization"


def read_secret(path):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path:
        raise ValueError("Unsafe upstream secret path")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as file:
        info = os.fstat(file.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_uid not in (0, os.getuid()) or info.st_size > 4097:
            raise ValueError("Upstream secret must be a protected regular file")
        secret = file.read().removesuffix(b"\n")
    if not re.fullmatch(rb"[!-~]{32,4096}", secret):
        raise ValueError("Invalid upstream secret")
    return secret


class TransportBoundary:
    def __init__(self, app, secret):
        self.app, self.expected = app, b"Bearer " + secret

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            return await self.app(scope, receive, send)
        if scope["type"] != "http":
            return await send({"type": "websocket.close", "code": 1008})
        headers = scope["headers"]
        transport = [v for k, v in headers if k.lower() == b"authorization"]
        native = [v for k, v in headers if k.lower() == CLIENT_AUTH]
        ingress = [v for k, v in headers if k.lower() == b"x-musia-ingress-ip"]
        peer = scope.get("client") or ("", 0)
        valid = (peer[0] == "127.0.0.1" and len(transport) == 1
                 and hmac.compare_digest(transport[0], self.expected))
        path = scope.get("path", "")
        valid = valid and (path == "/creator" or path.startswith("/creator/"))
        valid = valid and len(native) <= 1 and all(
            len(v) <= 256 and re.fullmatch(rb"Bearer [A-Za-z0-9._~+/-]{1,249}={0,2}", v)
            and not hmac.compare_digest(v, self.expected) for v in native)
        try:
            address = str(ipaddress.ip_address(ingress[0].decode())) if len(ingress) == 1 else None
        except (ValueError, UnicodeError):
            address = None
        valid = valid and address is not None
        if not valid:
            await send({"type": "http.response.start", "status": 401,
                        "headers": [(b"content-type", b"application/json"), (b"cache-control", b"no-store")]})
            return await send({"type": "http.response.body", "body": b'{"detail":"unauthorized_transport"}'})
        clean = [(k, v) for k, v in headers if k.lower() != b"authorization"
                 and not k.lower().startswith((b"x-lazyedge-", b"x-forwarded-"))
                 and k.lower() not in (CLIENT_AUTH, b"x-musia-ingress-ip", b"x-musia-upstream-authorization", b"forwarded")]
        if native:
            clean.append((b"authorization", native[0]))
        # Only the authenticated worker may assert the public HTTPS scheme.
        # This also keeps the /creator -> /creator/ framework redirect on HTTPS.
        await self.app({**scope, "headers": clean, "scheme": "https", "client": (address, 0),
                        "server": ("musia.lazying.art", 443)}, receive, send)


def create_app():
    # Importing the wrapper itself does not initialize SDKs, databases or models.
    from musia.creator.api import Settings, create_app as creator_app
    secret = read_secret(os.environ["MUSIA_CREATOR_UPSTREAM_SECRET_FILE"])
    settings = Settings.environment()
    if settings.origin != "https://musia.lazying.art":
        raise ValueError("Creator deployment requires its reviewed HTTPS origin")
    return TransportBoundary(creator_app(settings), secret)
