"""Real Node guards + TCP relay + ASGI transport boundary; no models or live ports."""
import ast
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import queue
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

# Loading the read-only learning controller must not generate bytecode there.
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy/creator"
HOST = "musia.lazying.art"
ID = "0123456789ab4cde8fab0123456789ab"
POLICY = json.loads((DEPLOY / "policy.json").read_text())


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


upstream = module("creator_upstream", DEPLOY / "upstream.py")
controller = module("creator_caddy", DEPLOY / "caddy_controller.py")


class Fixture(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 64

    def __init__(self, secret):
        super().__init__(("127.0.0.1", 0), Handler)
        self.requests = queue.Queue()
        self.holding = threading.Event()
        self.release = threading.Event()
        self.disconnected = threading.Event()
        self.behavior = "normal"
        self.boundary = upstream.TransportBoundary(self.app, secret.encode())

    async def app(self, scope, receive, send):
        body = (await receive())["body"]
        headers = dict(scope["headers"])
        self.requests.put((scope["path"], headers, body))
        if self.behavior == "hold":
            self.holding.set()
            self.release.wait(5)
        response = json.dumps({"path": scope["path"], "headers": {k.decode(): v.decode() for k, v in headers.items()},
                               "bytes": len(body)}).encode()
        status = 206 if b"range" in headers else 200
        extra = [(b"content-type", b"application/json"),
                 (b"set-cookie", b"__Secure-musia_creator=fixture; Path=/creator; Secure; HttpOnly; SameSite=Lax"),
                 (b"set-cookie", b"__Secure-musia_creator_binding=fixture; Path=/creator; Secure; HttpOnly"),
                 (b"x-musia-client-authorization", b"must-not-reflect"),
                 (b"authorization", b"must-not-reflect"),
                 (b"x-lazyedge-relay-authorization", b"must-not-reflect")]
        if status == 206:
            extra += [(b"content-range", b"bytes 0-9/100"), (b"accept-ranges", b"bytes")]
        if self.behavior == "stream":
            await send({"type": "http.response.start", "status": status, "headers": extra})
            for _ in range(80):
                try:
                    await send({"type": "http.response.body", "body": b"x", "more_body": True})
                except (BrokenPipeError, ConnectionResetError):
                    self.disconnected.set()
                    return
                time.sleep(.03)
            return
        extra.append((b"content-length", str(len(response)).encode()))
        await send({"type": "http.response.start", "status": status, "headers": extra})
        await send({"type": "http.response.body", "body": response})


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_GET(self):
        try:
            if self.headers.get("Transfer-Encoding") == "chunked":
                parts = []
                while True:
                    size = int(self.rfile.readline().strip(), 16)
                    if not size:
                        self.rfile.readline()
                        break
                    parts.append(self.rfile.read(size))
                    self.rfile.read(2)
                body = b"".join(parts)
            else:
                body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            scope = {"type": "http", "method": self.command, "path": self.path.split("?")[0],
                     "client": self.client_address,
                     "headers": [(k.lower().encode(), v.encode()) for k, v in self.headers.raw_items()]}

            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}

            async def send(msg):
                if msg["type"] == "http.response.start":
                    self.send_response(msg["status"])
                    for k, v in msg["headers"]:
                        self.send_header(k.decode(), v.decode())
                    self.send_header("Connection", "close")
                    self.end_headers()
                elif self.command != "HEAD":
                    self.wfile.write(msg.get("body", b""))
                    self.wfile.flush()
            asyncio.run(self.server.boundary(scope, receive, send))
        except (BrokenPipeError, ConnectionResetError, ValueError):
            self.server.disconnected.set()
        finally:
            self.close_connection = True

    do_POST = do_HEAD = do_DELETE = do_GET


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.relay, self.secret, self.native = [secrets.token_urlsafe(32) for _ in range(3)]
        self.app = Fixture(self.secret)
        self.thread = threading.Thread(target=self.app.serve_forever, daemon=True)
        self.thread.start()
        env = {**os.environ, "MUSIA_LAZYEDGE_ROOT": os.environ.get("MUSIA_LAZYEDGE_ROOT", "/home/lachlan/ProjectsLFS/LazyEdge")}
        self.process = subprocess.Popen(["node", str(DEPLOY / "fixtures/chain.mjs")], env=env,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.ports = {}
        self.addCleanup(self.cleanup)
        self.process.stdin.write(json.dumps({"relay": self.relay, "upstream": self.secret,
                                             "target": f"http://127.0.0.1:{self.app.server_port}", "timeoutMs": 1200}) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            self.fail("Local guard fixture failed to start")
        self.ports = json.loads(line)

    def cleanup(self):
        self.app.release.set()
        if self.process.poll() is None:
            try:
                self.process.communicate("stop\n", timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.communicate()
        self.app.shutdown()
        self.app.server_close()
        self.thread.join(2)
        for port in self.ports.values():
            with socket.socket() as sock:
                self.assertNotEqual(sock.connect_ex(("127.0.0.1", port)), 0, "Test listener leaked")

    def request(self, path="/creator/api/me", method="GET", headers=None, body=None, port="ingress", chunked=False):
        conn = http.client.HTTPConnection("127.0.0.1", self.ports[port] if isinstance(port, str) else port, timeout=5)
        try:
            conn.request(method, path, body, {"Host": HOST, **(headers or {})}, encode_chunked=chunked)
            response = conn.getresponse()
            return response.status, response.getheaders(), response.read()
        finally:
            conn.close()

    def trusted(self, **headers):
        return {"x-musia-ingress-ip": "192.0.2.10", **headers}

    def test_every_explicit_route_reaches_app(self):
        for method, path in POLICY["routes"]:
            with self.subTest(method=method, path=path):
                result = self.request(path.replace("{id}", ID), method)
                self.assertEqual(result[0], 200)

    def test_public_and_login_work_without_user_bearer(self):
        for method, path in [("GET", "/creator/api/songs"), ("POST", "/creator/auth/start"),
                             ("POST", "/creator/auth/native/start"), ("GET", "/creator/auth/callback?code=fixture&state=fixture")]:
            self.assertEqual(self.request(path, method)[0], 200)
            _, headers, _ = self.app.requests.get(timeout=1)
            self.assertNotIn(b"authorization", headers)

    def test_native_session_cookie_origin_request_and_range_survive(self):
        hdrs = {"Authorization": "Bearer " + self.native, "Cookie": "__Secure-musia_creator=fixture",
                "Origin": "https://" + HOST, "X-Musia-Request": "1", "Range": "bytes=0-9",
                "Content-Type": "application/json", "Idempotency-Key": "fixture"}
        status, response_headers, body = self.request(f"/creator/api/songs/{ID}/audio", headers=hdrs)
        self.assertEqual(status, 206)
        received = json.loads(body)["headers"]
        for name in ("authorization", "cookie", "origin", "x-musia-request", "range", "idempotency-key"):
            self.assertEqual(received[name], {k.lower(): v for k, v in hdrs.items()}[name])
        self.assertEqual(len([v for k, v in response_headers if k == "set-cookie"]), 2)
        self.assertEqual(dict(response_headers)["content-range"], "bytes 0-9/100")
        self.assertNotIn(self.secret.encode(), body)
        self.assertNotIn(self.relay.encode(), body)
        self.assertFalse(any(k.startswith("x-lazyedge-") or k == "x-musia-client-authorization" or k == "authorization" for k, _ in response_headers))

    def test_spoofed_dedicated_and_forwarding_headers_are_removed(self):
        headers = {"X-Musia-Client-Authorization": "Bearer attacker", "X-Musia-Upstream-Authorization": "Bearer attacker",
                   "X-Musia-Ingress-IP": "192.0.2.99", "X-LazyEdge-Relay-Authorization": "Bearer attacker",
                   "X-Forwarded-For": "192.0.2.99", "Forwarded": "for=attacker", "X-Real-IP": "attacker",
                   "X-Original-URL": "/admin", "X-HTTP-Method-Override": "DELETE"}
        status, _, body = self.request(headers=headers)
        self.assertEqual(status, 200)
        received = json.loads(body)["headers"]
        self.assertNotIn("authorization", received)
        for name in headers:
            self.assertNotIn(name.lower(), received)

    def test_default_deny_hosts_methods_paths_and_id_shapes(self):
        paths = ["/", "/healthz", "/api/v1/library", "/creatorx", "/creator/admin", "/creator/docs",
                 "/creator/api/jobs/" + ID, "/creator/api/songs/not-a-uuid", "/creator/api/songs/" + ID.upper(),
                 "/creator/api/songs/01234567-89ab-4cde-8fab-0123456789ab", "/creator/api/songs/" + ID + "/reactions/delete",
                 "/creator/api/songs/" + ID + "/", "/creator/%2e%2e/admin", "/creator/%252e%252e/admin",
                 "/creator//api/me", "/creator/api%2fsongs", "/creator/../api/me", "/creator/api\\songs",
                 "/creator/%61pi/me", "/creator/api/me%00", "/creator/api/me#fragment"]
        for path in paths:
            with self.subTest(path=path):
                self.assertIn(self.request(path, headers=self.trusted(), port="edge")[0], (400, 404))
        for method in ("PUT", "PATCH", "OPTIONS", "TRACE", "HEAD"):
            self.assertIn(self.request(method=method)[0], (400, 404, 405))
        for host in ("wrong.example", HOST + ".", HOST + ":8080", "127.0.0.1"):
            self.assertEqual(self.request(headers={"Host": host})[0], 400)
        self.assertTrue(self.app.requests.empty())

    def test_transport_tokens_never_authorize_users_and_direct_ports_fail(self):
        for value in (self.relay, self.secret):
            self.assertEqual(self.request(headers={"Authorization": "Bearer " + value})[0], 401)
        for port in ("worker", "tunnel"):
            for relay in (None, "Bearer wrong", "Bearer " + self.secret):
                headers = self.trusted()
                if relay: headers["x-lazyedge-relay-authorization"] = relay
                self.assertEqual(self.request(port=port, headers=headers)[0], 401)
        self.assertEqual(self.request(port="edge", headers=self.trusted(Authorization="Bearer " + self.native))[0], 400)
        self.assertEqual(self.request(port=self.app.server_port)[0], 401)
        self.assertTrue(self.app.requests.empty())

    def test_worker_rechecks_routes_and_rejects_duplicate_transport(self):
        headers = self.trusted(**{"x-lazyedge-relay-authorization": "Bearer " + self.relay})
        for path, method in [("/creator/admin", "GET"), ("/creator/api/me", "PUT"),
                             ("/creator/%2e%2e/admin", "GET"), ("/api/v1/library", "GET")]:
            self.assertIn(self.request(path, method, headers=headers, port="worker")[0], (400, 404))
        self.assertEqual(self.request(headers={**headers, "Host": "wrong.example"}, port="worker")[0], 400)
        with socket.create_connection(("127.0.0.1", self.ports["worker"]), timeout=3) as sock:
            wire = (f"GET /creator/api/me HTTP/1.1\r\nHost: {HOST}\r\nX-Musia-Ingress-IP: 192.0.2.10\r\n"
                    f"X-LazyEdge-Relay-Authorization: Bearer {self.relay}\r\n"
                    f"X-LazyEdge-Relay-Authorization: Bearer {self.relay}\r\nConnection: close\r\n\r\n")
            sock.sendall(wire.encode())
            self.assertIn(b" 401 ", sock.recv(4096).split(b"\r\n")[0])
        self.assertTrue(self.app.requests.empty())

    def test_duplicate_native_header_and_non_bearer_auth_fail_closed(self):
        for native in ("Basic fixture", "Bearer bad token", "Bearer " + "x" * 260):
            self.assertEqual(self.request(headers={"Authorization": native})[0], 400)
        with socket.create_connection(("127.0.0.1", self.ports["edge"]), timeout=3) as sock:
            wire = (f"GET /creator/api/me HTTP/1.1\r\nHost: {HOST}\r\nX-Musia-Ingress-IP: 192.0.2.10\r\n"
                    "X-Musia-Client-Authorization: Bearer one\r\nX-Musia-Client-Authorization: Bearer two\r\nConnection: close\r\n\r\n")
            sock.sendall(wire.encode())
            self.assertIn(b" 400 ", sock.recv(4096).split(b"\r\n")[0])
        self.assertTrue(self.app.requests.empty())

    def test_body_exact_limit_and_overflow_including_chunked(self):
        for chunked in (False, True):
            body = [b"x" * 24000, b"x" * 24000] if chunked else b"x" * 48000
            self.assertEqual(self.request("/creator/api/jobs", "POST", body=body, chunked=chunked)[0], 200)
            body = [b"x" * 24000, b"x" * 24001] if chunked else b"x" * 48001
            self.assertEqual(self.request("/creator/api/jobs", "POST", body=body, chunked=chunked)[0], 413)

    def test_ip_auth_and_general_limits_and_independent_ips(self):
        for n in range(21):
            status = self.request("/creator/auth/start", "POST", headers=self.trusted(), port="edge")[0]
            self.assertEqual(status, 200 if n < 20 else 429)
        for n in range(241):
            status = self.request(headers={"x-musia-ingress-ip": "192.0.2.11"}, port="edge")[0]
            self.assertEqual(status, 200 if n < 240 else 429)
        self.assertEqual(self.request(headers={"x-musia-ingress-ip": "192.0.2.12"}, port="edge")[0], 200)

    def test_32_concurrent_and_deadline_releases_slots(self):
        self.app.behavior = "hold"
        self.app.request_queue_size = 64
        with ThreadPoolExecutor(max_workers=32) as pool:
            futures = [pool.submit(self.request) for _ in range(32)]
            limit = time.monotonic() + 1
            while self.app.requests.qsize() < 32 and time.monotonic() < limit:
                time.sleep(.01)
            self.assertEqual(self.request()[0], 429)
            self.app.release.set()
            self.assertTrue(all(f.result()[0] == 200 for f in futures))
        self.assertEqual(self.request()[0], 200)

    def test_timeout_and_tunnel_loss_recover(self):
        self.app.behavior = "hold"
        started = time.monotonic()
        self.assertEqual(self.request()[0], 503)
        self.assertLess(time.monotonic() - started, 2.5)
        self.app.release.set()
        self.app.behavior = "normal"
        self.process.stdin.write("drop\n"); self.process.stdin.flush()
        self.assertEqual(self.process.stdout.readline().strip(), "dropped")
        self.assertEqual(self.request()[0], 503)
        self.process.stdin.write("restore\n"); self.process.stdin.flush()
        self.assertEqual(self.process.stdout.readline().strip(), "restored")
        self.assertEqual(self.request()[0], 200)

    def test_stream_deadline_and_client_disconnect_abort_upstream(self):
        self.app.behavior = "stream"
        conn = http.client.HTTPConnection("127.0.0.1", self.ports["ingress"], timeout=4)
        conn.request("GET", "/creator/api/me", headers={"Host": HOST})
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        response.read(1)
        response.close(); conn.close()
        self.assertTrue(self.app.disconnected.wait(2.5))
        self.app.disconnected.clear()
        started = time.monotonic()
        try:
            self.request()
        except (http.client.IncompleteRead, ConnectionResetError):
            pass
        self.assertLess(time.monotonic() - started, 2.5)
        self.assertTrue(self.app.disconnected.wait(1))


class ContractTests(unittest.TestCase):
    def test_allowlist_matches_current_backend(self):
        tree = ast.parse((ROOT / "musia/creator/api.py").read_text())
        expected = set()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute) or not isinstance(dec.func.value, ast.Name) or dec.func.value.id != "app":
                    continue
                if dec.func.attr not in ("get", "post", "delete", "api_route"):
                    continue
                path = ast.literal_eval(dec.args[0])
                methods = [dec.func.attr.upper()] if dec.func.attr != "api_route" else ast.literal_eval(next(k.value for k in dec.keywords if k.arg == "methods"))
                for key in ("song", "job", "comment", "account"):
                    path = path.replace("{" + key + "}", "{id}")
                for method in methods:
                    for kind in ("like", "save") if "{kind}" in path else (None,):
                        expected.add((method, "/creator" + (path.replace("{kind}", kind) if kind else path)))
        expected.update(("GET", "/creator" + path) for path in ("", "/", "/app.js", "/native-return.js", "/styles.css", "/terms"))
        self.assertEqual(expected, set(map(tuple, POLICY["routes"])))

    def test_app_transport_rejects_wrong_peer_duplicate_and_transport_as_session(self):
        async def exercise(headers, peer="127.0.0.1", path="/creator/api/me"):
            result = []
            async def app(scope, receive, send):
                result.append(scope)
            async def send(msg):
                result.append(msg)
            guard = upstream.TransportBoundary(app, b"u" * 40)
            await guard({"type": "http", "path": path, "client": (peer, 1), "headers": headers}, None, send)
            return result
        valid = [(b"authorization", b"Bearer " + b"u" * 40), (b"x-musia-ingress-ip", b"192.0.2.3")]
        for headers, peer, path in [(valid, "192.0.2.1", "/creator/api/me"), (valid + valid, "127.0.0.1", "/creator/api/me"),
                                    (valid, "127.0.0.1", "/api/v1/library"),
                                    (valid + [(upstream.CLIENT_AUTH, valid[0][1])], "127.0.0.1", "/creator/api/me")]:
            self.assertEqual(asyncio.run(exercise(headers, peer, path))[0]["status"], 401)
        accepted = asyncio.run(exercise(valid))[0]
        self.assertEqual(accepted["scheme"], "https")
        self.assertEqual(accepted["client"], ("192.0.2.3", 0))
        self.assertEqual(asyncio.run(exercise(valid[:1]))[0]["status"],401)
        self.assertEqual(asyncio.run(exercise(valid[:1]+[(b"x-musia-ingress-ip",b"invalid")]))[0]["status"],401)
        self.assertNotIn((b"authorization", valid[0][1]), accepted["headers"])

    def test_protected_secret_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "secret"
            path.write_bytes(secrets.token_urlsafe(32).encode())
            path.chmod(0o600)
            self.assertTrue(upstream.read_secret(path))
            path.chmod(0o644)
            with self.assertRaises(ValueError): upstream.read_secret(path)
            path.chmod(0o600)
            link = Path(directory) / "link"
            link.symlink_to(path)
            with self.assertRaises(ValueError): upstream.read_secret(link)

    def test_node_protected_files_and_separate_role_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "secret"
            path.write_text(secrets.token_urlsafe(32))
            path.chmod(0o600)
            code = """
                import { privateText, startGuard } from './deploy/creator/gateway.mjs';
                const value = await privateText(process.argv[1]);
                try { await startGuard({role: 'worker', relayToken: value, upstreamToken: value}); process.exit(8); }
                catch {}
                try { await startGuard({role: 'edge', relayToken: value, upstreamToken: value}); process.exit(9); }
                catch {}
            """
            env = {**os.environ, "MUSIA_LAZYEDGE_ROOT": os.environ.get("MUSIA_LAZYEDGE_ROOT", "/home/lachlan/ProjectsLFS/LazyEdge")}
            result = subprocess.run(["node", "--input-type=module", "-e", code, str(path)], cwd=ROOT,
                                    env=env, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 0)
            path.chmod(0o644)
            result = subprocess.run(["node", "--input-type=module", "-e", code, str(path)], cwd=ROOT,
                                    env=env, capture_output=True, timeout=5)
            self.assertNotEqual(result.returncode, 0)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "Caddyfile"
        self.before = ("{\n    admin 127.0.0.1:12019\n    https_port 18443\n}\nother.example {\n    respond ok\n}\n" +
                       controller.SITE.replace("ROUTE_LIST", "/ /healthz /api/v1/library") + "\nlast.example {\n    respond ok\n}\n").encode()
        self.config.write_bytes(self.before)
        self.config.chmod(0o644)
        self.tx = self.root / "transaction"
        self.tx.mkdir(mode=0o700)
        self.ok = [sys.executable, "-c", "pass"]

    def apply(self, **kwargs):
        return controller.transact("apply", self.config, self.tx, controller.sha(self.before),
                                   kwargs.get("validate", self.ok), kwargs.get("reload", self.ok), kwargs.get("probe", self.ok))

    def test_exact_patch_preserves_learning_and_other_hosts_and_rolls_back(self):
        candidate = controller.render(self.before)
        self.assertEqual(candidate.replace(controller.INSERT.encode(), b"", 1).replace(controller.SCOPED.encode(), controller.ANCHOR.encode(), 1), self.before)
        self.assertEqual(controller.render(candidate), candidate)
        self.assertLess(candidate.index(b"handle @musia_creator"), candidate.index(b"max_size 1KB"))
        digest = self.apply()
        self.assertEqual(self.config.read_bytes(), candidate)
        self.assertEqual((self.tx / "Caddyfile.before").stat().st_mode & 0o777, 0o600)
        controller.transact("rollback", self.config, self.tx, digest, self.ok, self.ok, self.ok)
        self.assertEqual(self.config.read_bytes(), self.before)

    def test_template_is_the_existing_learning_controller_template(self):
        learning = module("learning_controller", ROOT / "deploy/learning/remote.py")
        release = self.root / "learning"
        release.mkdir()
        (release / "release.json").write_text(json.dumps({"staticPaths": ["/"], "songIds": ["fixture"]}))
        original = learning.site_block(release).encode()
        self.assertIn(b"127.0.0.1:18896", controller.render(original))

    def test_ambiguous_changed_templates_and_symlinks_are_refused(self):
        for content in (self.before + self.before, self.before.replace(b"max_size 1KB", b"max_size 2KB"),
                        self.before.replace(b"127.0.0.1:18440", b"127.0.0.1:9999"), self.before + b"\nmusia.lazying.art {}\n"):
            with self.assertRaises(ValueError): controller.render(content)
        with self.assertRaises(ValueError):
            controller.transact("apply", self.config, self.tx, "0" * 64, self.ok, self.ok, self.ok)
        link = self.root / "link"
        link.symlink_to(self.config)
        with self.assertRaises(ValueError): controller.read_regular(link)
        self.assertEqual(self.config.read_bytes(), self.before)

    def test_failed_validation_leaves_original_and_failed_probe_restores_it(self):
        fail = [sys.executable, "-c", "raise SystemExit(1)"]
        with self.assertRaises(RuntimeError): self.apply(validate=fail)
        self.assertEqual(self.config.read_bytes(), self.before)
        self.tx = self.root / "second"
        self.tx.mkdir(mode=0o700)
        marker = self.root / "failed_once"
        probe = [sys.executable, "-c", "import pathlib,sys; p=pathlib.Path(sys.argv[1]); existed=p.exists(); p.touch(); sys.exit(0 if existed else 1)", str(marker)]
        with self.assertRaises(RuntimeError): self.apply(probe=probe)
        self.assertEqual(self.config.read_bytes(), self.before)

    def test_concurrent_writer_is_never_overwritten(self):
        writer = [sys.executable, "-c", "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('other writer')", str(self.config)]
        with self.assertRaises(ValueError): self.apply(validate=writer)
        self.assertEqual(self.config.read_text(), "other writer")

    def test_concurrent_writer_during_acceptance_is_not_rolled_back_over(self):
        writer = [sys.executable, "-c", "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('other writer')", str(self.config)]
        with self.assertRaises(ValueError): self.apply(probe=writer)
        self.assertEqual(self.config.read_text(), "other writer")

    def test_import_mutation_refuses_apply_and_bad_import_shapes(self):
        imported = self.root / "imported.caddy"
        imported.write_text("# fixture literal import\n")
        imported.chmod(0o600)
        self.before = f"import {imported}\n".encode() + self.before
        self.config.write_bytes(self.before)
        writer = [sys.executable, "-c", "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('# concurrent import')", str(imported)]
        with self.assertRaises(ValueError): self.apply(validate=writer)
        self.assertEqual(self.config.read_bytes(), self.before)
        for line in ("import /tmp/*.caddy\n", "import snippet\n"):
            with self.assertRaises(ValueError): controller.imports(line.encode())


if __name__ == "__main__":
    unittest.main()
