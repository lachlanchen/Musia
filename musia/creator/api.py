"""Separate creator boundary; never mounts Studio or accepts worker commands."""

from dataclasses import dataclass
from html import escape
import os
from pathlib import Path
import secrets
from urllib.parse import urlencode, urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response

from musia.learning import ROOT, _base_url, create_app as learning_app
from .agent import Producer
from .auth import CentralAuth
from .contracts import Chat, Comment, CreatorError, Generate, Invite, PLANS, Reaction, Report, TERMS_VERSION, Visibility
from .store import Store, digest
from .native_auth import NativeFlow, NativeStart, NativeExchange
from .billing import Billing, Verification


@dataclass(frozen=True)
class Settings:
    origin: str = "http://127.0.0.1:8796"
    directory: Path = Path.home() / ".local/share/musia/creator"
    generation_enabled: bool = False
    invitation_required: bool = True
    auth_directory: Path | None = None

    def __post_init__(self):
        _base_url(self.origin)
        if self.origin.endswith("/"):
            raise ValueError("Origin must not end with slash")

    @classmethod
    def environment(cls):
        return cls(origin=os.environ.get("MUSIA_CREATOR_ORIGIN", "http://127.0.0.1:8796"),
                   directory=Path(os.environ.get("MUSIA_CREATOR_DATA", str(Path.home()/".local/share/musia/creator"))),
                   generation_enabled=os.environ.get("MUSIA_CREATOR_GENERATION") == "1",
                   invitation_required=os.environ.get("MUSIA_CREATOR_OPEN_SIGNUP") != "1",
                   auth_directory=Path(os.environ["MUSIA_CREATOR_AUTH_DIR"]) if os.environ.get("MUSIA_CREATOR_AUTH_DIR") else None)


class Boundary:
    def __init__(self, app, origin):
        self.app, self.origin = app, origin

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {k.lower(): v for k, v in scope["headers"]}

        async def secure(message):
            if message["type"] == "http.response.start":
                message["headers"] += [(b"cache-control", b"no-store"), (b"referrer-policy", b"no-referrer"),
                                       (b"x-content-type-options", b"nosniff"), (b"x-frame-options", b"DENY"),
                                       (b"content-security-policy", b"default-src 'self'; img-src 'self'; media-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")]
            await send(message)

        error = None
        if headers.get(b"host", b"").decode() != urlsplit(self.origin).netloc:
            error = (400, "invalid_host")
        elif scope["method"] not in ("GET", "HEAD", "POST", "DELETE"):
            error = (405, "method_not_allowed")
        elif scope["method"] in ("POST", "DELETE") and (
            not (headers.get(b"origin", b"").decode() == self.origin or (
                b"origin" not in headers and (headers.get(b"authorization", b"").startswith(b"Bearer ") or
                scope["path"].removeprefix("/creator") in ("/auth/native/start", "/auth/native/exchange"))
            )) or headers.get(b"x-musia-request") != b"1"
            or headers.get(b"content-type", b"").split(b";")[0] != b"application/json"
        ):
            error = (403, "same_origin_request_required")
        if error:
            return await JSONResponse({"detail": error[1]}, status_code=error[0])(scope, receive, secure)
        # Bound the whole body, including chunked uploads, before FastAPI parses it.
        chunks, length = [], 0
        while True:
            msg = await receive()
            if msg["type"] == "http.disconnect":
                return
            length += len(msg.get("body", b""))
            if length > 48000:
                return await JSONResponse({"detail": "request_too_large"}, status_code=413)(scope, receive, secure)
            chunks.append(msg)
            if not msg.get("more_body"):
                break

        async def replay():
            return chunks.pop(0) if chunks else await receive()

        await self.app(scope, replay, secure)


def create_app(settings=None, *, store=None, auth=None, producer=None, billing=None):
    cfg = settings or Settings.environment()
    store = store or Store(cfg.directory)
    auth = auth or (CentralAuth(cfg.auth_directory, cfg.origin) if cfg.auth_directory else None)
    producer = producer or Producer()
    native = NativeFlow(store)
    billing = billing or Billing(store)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, redirect_slashes=False)
    app.add_middleware(Boundary, origin=cfg.origin)
    secure = cfg.origin.startswith("https:")
    cookie = "__Secure-musia_creator" if secure else "musia_creator_local"
    binding_cookie = cookie + "_binding"

    @app.exception_handler(CreatorError)
    async def error_handler(request, exc):
        return JSONResponse({"detail": exc.code}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request, exc):
        # Do not echo submitted lyrics, codes or account data in errors.
        return JSONResponse({"detail": "invalid_request"}, status_code=422)

    def session_token(request):
        authorization = request.headers.get("authorization")
        if authorization is not None:
            if not authorization.startswith("Bearer ") or len(authorization) > 256:
                raise CreatorError("sign_in_required", 401)
            return authorization[7:]
        return request.cookies.get(cookie, "")

    def session(request, optional=False):
        token = session_token(request)
        if not token and optional:
            return None
        if not auth:
            raise CreatorError("sign_in_unavailable", 503)
        try:
            result = store.session(token)
            auth.verify(result)
            return result
        except CreatorError as exc:
            if optional and exc.status == 401:
                return None
            raise

    def owner(request, optional=False):
        result = session(request, optional)
        return result["owner"] if result else None

    def set_cookie(response, name, token, max_age):
        response.set_cookie(name, token, max_age=max_age, secure=secure, httponly=True, samesite="lax", path="/creator")

    @app.get("/api/capabilities")
    def capabilities():
        providers = auth.providers() if auth else {}
        connected = any(value is True for value in providers.values())
        return {"version": 1, "providers": providers, "login": connected,
                "generation": cfg.generation_enabled and connected, "agent": producer.available and connected,
                "invitationRequired": cfg.invitation_required, "salesEnabled": billing.sales_available, "termsVersion": TERMS_VERSION,
                "plans": [{"id": k, **v, "priceStatus": "store_qualification_required"} for k, v in PLANS.items()]}

    @app.post("/auth/start")
    def login(request: Request):
        if not auth:
            raise CreatorError("sign_in_unavailable", 503)
        with store.db() as db:
            # Trust only the direct peer; reverse proxy must add its own per-IP limits.
            store.rate(db, digest(request.client.host if request.client else "unknown"), "login", 100)
        binding = secrets.token_urlsafe(32)
        response = JSONResponse({"url": auth.begin(binding)})
        set_cookie(response, binding_cookie, binding, 600)
        return response

    @app.post("/auth/native/start")
    def native_start(body: NativeStart, request: Request):
        if not auth or not auth.providers():
            raise CreatorError("sign_in_unavailable", 503)
        attempt = native.start(body, request.client.host if request.client else "unknown")
        return {"attempt": attempt, "url": cfg.origin + "/creator/auth/native/browser?attempt=" + attempt, "expiresIn": 600}

    @app.get("/auth/native/browser")
    def native_browser(request: Request, attempt: str = ""):
        if not auth:
            raise CreatorError("sign_in_unavailable", 503)
        binding = secrets.token_urlsafe(32)
        native.browser(attempt, binding)
        response = RedirectResponse(auth.begin(binding), status_code=303)
        set_cookie(response, binding_cookie, binding, 600)
        return response

    @app.post("/auth/native/exchange")
    def native_exchange(body: NativeExchange):
        return native.exchange(body)

    @app.get("/auth/callback")
    def callback(request: Request):
        if not auth:
            raise CreatorError("sign_in_unavailable", 503)
        binding = request.cookies.get(binding_cookie, "")
        if not binding:
            raise CreatorError("sign_in_expired", 401)
        token = auth.complete(cfg.origin + "/creator/auth/callback?" + request.url.query, binding, store)
        completion = native.finish(binding, token)
        if completion:
            # End the issuer's form redirect chain on HTTPS. Redirecting directly
            # to a custom scheme inherits its form-action CSP and is blocked.
            destination = escape("art.lazying.musia://auth?" + urlencode(completion), quote=True)
            response = HTMLResponse('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>Return to Musia</title><link rel="stylesheet" href="/creator/styles.css">'
                '<script defer src="/creator/native-return.js"></script></head><body>'
                '<main class="auth-return"><h1>Musia</h1><p>Sign-in complete.</p>'
                f'<a id="native-return" href="{destination}">Return to Musia</a></main></body></html>')
        else:
            response = RedirectResponse("/creator/", status_code=303)
        response.delete_cookie(binding_cookie, path="/creator", secure=secure, httponly=True, samesite="lax")
        if not completion:
            set_cookie(response, cookie, token, 86400*7)
        return response

    @app.post("/auth/logout")
    def logout(request: Request):
        token = session_token(request)
        try:
            current = store.session(token)
        except CreatorError:
            current = None
        store.logout(token)
        if auth and current:
            auth.sign_out(current)
        response = JSONResponse({"ok": True})
        response.delete_cookie(cookie, path="/creator", secure=secure, httponly=True, samesite="lax")
        return response

    @app.get("/api/me")
    def me(request: Request):
        account = owner(request, True)
        return {"account": store.profile(account) if account else None}

    @app.get("/api/billing")
    def billing_status(request: Request):
        return billing.status(owner(request))

    @app.post("/api/billing/verify")
    def billing_verify(body: Verification, request: Request):
        return billing.verify(owner(request), body)

    @app.post("/api/billing/restore")
    def billing_restore(request: Request):
        return billing.restore(owner(request))

    @app.post("/api/terms")
    def terms(request: Request):
        store.accept_terms(owner(request))
        return {"ok": True}

    @app.post("/api/invitations/redeem")
    def invite(body: Invite, request: Request):
        store.redeem(owner(request), body.code)
        return {"ok": True}

    @app.post("/api/agent")
    def agent(body: Chat, request: Request):
        account = owner(request)
        if not producer.available:
            raise CreatorError("agent_not_connected", 503)
        turn = store.start_turn(account, body.model_dump_json(), invitation_required=cfg.invitation_required)
        try:
            answer = producer.refine(body)
            store.finish_turn(account, turn, answer.model_dump_json())
            return answer.model_dump()
        except Exception:
            store.finish_turn(account, turn, None)
            raise CreatorError("agent_response_unavailable", 503) from None

    @app.post("/api/jobs")
    def generate(body: Generate, request: Request):
        account = owner(request)
        if not cfg.generation_enabled:
            raise CreatorError("generation_not_connected", 503)
        return store.submit(account, request.headers.get("idempotency-key", ""), body, invitation_required=cfg.invitation_required)

    @app.get("/api/jobs")
    def jobs(request: Request):
        return {"jobs": store.jobs(owner(request))}

    @app.post("/api/jobs/{job}/cancel")
    def cancel(job: str, request: Request):
        store.cancel(owner(request), job)
        return {"ok": True}

    @app.get("/api/songs")
    def songs(request: Request, mode: str = "public"):
        if mode not in ("public", "mine", "saved"):
            raise CreatorError("invalid_library")
        return {"songs": store.songs(owner(request, True), mode)}

    @app.get("/api/songs/{song}")
    def song(song: str, request: Request):
        return store.song(song, owner(request, True))

    @app.api_route("/api/songs/{song}/audio", methods=["GET", "HEAD"])
    def audio(song: str, request: Request):
        row = store.audio(song, owner(request, True))
        path = cfg.directory / "artifacts" / song / "song.wav"
        if not row or path.is_symlink() or not path.is_file() or path.resolve() != path.absolute() or str(path) != row["audio"]:
            raise CreatorError("audio_unavailable", 404)
        # No bucket URL bypass: visibility checked on every request, including ranges.
        return FileResponse(path, media_type="audio/wav", filename="song.wav", content_disposition_type="inline")

    @app.post("/api/songs/{song}/visibility")
    def visibility(song: str, body: Visibility, request: Request):
        store.visibility(owner(request), song, body.visibility)
        return {"ok": True}

    @app.post("/api/songs/{song}/reactions/{kind}")
    def reaction(song: str, kind: str, body: Reaction, request: Request):
        store.react(owner(request), song, kind, body.active)
        return {"ok": True}

    @app.get("/api/songs/{song}/comments")
    def comments(song: str, request: Request):
        return {"comments": store.comments(song, owner(request, True))}

    @app.post("/api/songs/{song}/comments")
    def comment(song: str, body: Comment, request: Request):
        return {"id": store.comment(owner(request), song, body.text), "state": "pending"}

    @app.delete("/api/comments/{comment}")
    def remove_comment(comment: str, request: Request):
        store.remove_comment(owner(request), comment)
        return {"ok": True}

    @app.post("/api/songs/{song}/reports")
    def report(song: str, body: Report, request: Request):
        store.report(owner(request), song, body.reason)
        return {"ok": True}

    @app.post("/api/accounts/{account}/block")
    def block(account: str, body: Reaction, request: Request):
        store.block(owner(request), account, body.active)
        return {"ok": True}

    @app.get("/api/blocks")
    def blocks(request: Request):
        return {"accounts": store.blocks(owner(request))}

    @app.delete("/api/me")
    def delete_account(request: Request):
        current = session(request)
        store.delete_account(current["owner"])
        auth.delete_links(current)
        response = JSONResponse({"ok": True, "mediaPurge": "scheduled_after_active_render"})
        response.delete_cookie(cookie, path="/creator", secure=secure, httponly=True, samesite="lax")
        return response

    files = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
             "/native-return.js": ("native-return.js", "text/javascript"),
             "/styles.css": ("styles.css", "text/css"), "/terms": ("terms.html", "text/html")}

    def static(request: Request):
        path = request.url.path.removeprefix("/creator")
        filename, media_type = files[path]
        return Response((ROOT / "apps/web/creator" / filename).read_bytes(), media_type=media_type)

    for path in files:
        app.add_api_route(path, static, methods=["GET"], include_in_schema=False)

    root = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    root.mount("/creator", app)
    root.mount("/", learning_app(public_base_url=cfg.origin))
    return root
