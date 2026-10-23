"""Text backends cannot change account, render, filesystem or provider authority."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import httpx

from musia.creator.agent import Producer, private_endpoint, read_secret
from musia.creator.contracts import Chat, CreatorError, Draft


REPLY = {"message": "Review this draft before rendering.", "brief": Draft(title="Home", bpm=82).model_dump()}
ENV = {"MUSIA_CREATOR_TEXT_MODEL": "test-model", "MUSIA_CREATOR_TEXT_API_KEY": "private-test-key",
       "MUSIA_CREATOR_TEXT_BASE_URL": "https://api.deepseek.com"}


class BackendTests(unittest.TestCase):
    def producer(self, **extra):
        with patch.dict(os.environ, {**ENV, **extra}, clear=True):
            return Producer()

    def transport(self, producer, handler):
        original = httpx.AsyncClient

        def factory(**kwargs):
            self.assertFalse(kwargs["trust_env"])
            self.assertFalse(kwargs["follow_redirects"])
            return original(**kwargs, transport=httpx.MockTransport(handler))
        return patch("httpx.AsyncClient", side_effect=factory)

    def test_direct_preserves_context_without_tool_authority(self):
        def handle(request):
            self.assertEqual(str(request.url), "https://api.deepseek.com/chat/completions")
            payload = json.loads(request.content)
            self.assertNotIn("tools", payload)
            self.assertEqual(payload["model"], "test-model")
            self.assertEqual(json.loads(payload["messages"][1]["content"])["brief"]["bpm"], 82)
            return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(REPLY)}}]})
        producer = self.producer()
        with self.transport(producer, handle):
            self.assertEqual(producer.refine(Chat(message="Warm chorus", brief=Draft(bpm=82))).brief.title, "Home")

    def test_proxy_explicit_not_ambient(self):
        producer = self.producer(HTTPS_PROXY="http://untrusted:99")
        self.assertEqual(producer.proxy, "")

    def test_thinking_is_an_explicit_server_setting_for_deepseek_only(self):
        producer = self.producer(MUSIA_CREATOR_DEEPSEEK_THINKING="disabled")
        with patch.object(producer, "_post", return_value={"choices":[{"finish_reason":"stop", "message":{"content":json.dumps(REPLY)}}]}) as post:
            producer.refine(Chat(message="A song"))
            self.assertEqual(post.call_args.args[1]["thinking"], {"type":"disabled"})
        self.assertEqual(self.producer().thinking, "")
        with self.assertRaises(ValueError):
            self.producer(MUSIA_CREATOR_DEEPSEEK_THINKING="unbounded")

    def test_private_endpoints_deny_ssrf_and_authority_override(self):
        for url in ("http://169.254.169.254:8081", "http://agent:8081/path", "http://agent:8081?x=1",
                    "http://user@agent:8081", "https://agent:8081", "http://agent:80", "http://agent.evil:8081"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                private_endpoint(url, "agent", 8081)
        self.assertEqual(private_endpoint("http://agent:8081", "agent", 8081), "http://agent:8081")

    def test_unknown_backend_fails_closed(self):
        with self.assertRaises(ValueError):
            self.producer(MUSIA_CREATOR_TEXT_BACKEND="shell")

    def test_secret_files_and_conflicting_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key"
            path.write_text("test-key\n")
            with patch.dict(os.environ, {"KEY_FILE": str(path)}, clear=True):
                self.assertEqual(read_secret("KEY"), "test-key")
            with patch.dict(os.environ, {"KEY_FILE": str(path), "KEY": "other"}, clear=True), self.assertRaises(ValueError):
                read_secret("KEY")
            path.write_text("x" * 8193)
            with patch.dict(os.environ, {"KEY_FILE": str(path)}, clear=True), self.assertRaises(ValueError):
                read_secret("KEY")

    def test_aginti_sends_only_existing_bounded_chat_and_revalidates_reply(self):
        producer = self.producer(MUSIA_CREATOR_TEXT_BACKEND="aginti", MUSIA_CREATOR_AGINTI_URL="http://agent:8081",
                                 MUSIA_CREATOR_AGINTI_TOKEN="a"*32)
        self.assertTrue(producer.available)
        self.assertEqual(producer.key, "")
        def handle(request):
            self.assertEqual(str(request.url), "http://agent:8081/v1/refine")
            self.assertEqual(request.headers["authorization"], "Bearer " + "a"*32)
            self.assertEqual(set(json.loads(request.content)), {"message", "history", "brief", "focus", "reference"})
            self.assertEqual(json.loads(request.content)['focus'], 'create')
            return httpx.Response(200, json=REPLY)
        with self.transport(producer, handle):
            self.assertEqual(producer.refine(Chat(message="A song")).brief.bpm, 82)
        with self.transport(producer, lambda _: httpx.Response(200, json={**REPLY, "command": "bad"})), self.assertRaises(CreatorError):
            producer.refine(Chat(message="A song"))

    def test_incomplete_tool_refusal_and_malformed_results_never_succeed(self):
        producer = self.producer()
        for value in (
            {"choices": [{"finish_reason": "length", "message": {"content": json.dumps(REPLY)}}]},
            {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(REPLY), "tool_calls": ["x"]}}]},
            {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(REPLY), "refusal": "no"}}]},
            {"choices": [{"finish_reason": "stop", "message": {"content": "not JSON"}}]},
        ):
            with self.subTest(value=value), self.transport(producer, lambda _: httpx.Response(200, json=value)), self.assertRaises(CreatorError):
                producer.refine(Chat(message="A song"))

    def test_errors_and_redirects_not_retried_or_exposed(self):
        producer = self.producer()
        for status in (302, 401, 429, 500, 503):
            calls = []
            def handle(request):
                calls.append(request)
                return httpx.Response(status, headers={"location": "http://169.254.169.254"}, text="private-test-key")
            with self.transport(producer, handle), self.assertRaises(CreatorError) as raised:
                producer.refine(Chat(message="A song"))
            self.assertEqual(str(raised.exception), "agent_response_unavailable")
            self.assertEqual(len(calls), 1)

    def test_large_response_rejected(self):
        producer = self.producer()
        with self.transport(producer, lambda _: httpx.Response(200, content=b" "*65537)), self.assertRaises(CreatorError):
            producer.refine(Chat(message="A song"))

    def test_slow_response_has_a_whole_request_deadline(self):
        import anyio
        class Slow(httpx.AsyncByteStream):
            async def __aiter__(self):
                await anyio.sleep(1)
                yield b"{}"
        producer = self.producer()
        producer.timeout = 0.02
        with self.transport(producer, lambda _: httpx.Response(200, stream=Slow())), self.assertRaises(CreatorError):
            producer.refine(Chat(message="A song"))

    def test_concurrency_limit_released_after_error(self):
        producer = self.producer(MUSIA_CREATOR_TEXT_CONCURRENCY="1")
        self.assertTrue(producer._slots.acquire(blocking=False))
        with self.assertRaisesRegex(CreatorError, "agent_busy"):
            producer.refine(Chat(message="A song"))
        producer._slots.release()
        with patch.object(producer, "_post", side_effect=RuntimeError("secret")), self.assertRaises(CreatorError):
            producer.refine(Chat(message="A song"))
        self.assertTrue(producer._slots.acquire(blocking=False))
        producer._slots.release()

    def test_resource_limits_are_validated(self):
        for key, value in (("MUSIA_CREATOR_TEXT_TIMEOUT", "1000"), ("MUSIA_CREATOR_TEXT_CONCURRENCY", "0")):
            with self.assertRaises(ValueError): self.producer(**{key: value})

    def test_missing_credentials_do_not_select_another_backend(self):
        producer = self.producer(MUSIA_CREATOR_TEXT_API_KEY="")
        self.assertFalse(producer.available)
        with self.assertRaisesRegex(CreatorError, "agent_not_connected"):
            producer.refine(Chat(message="A song"))


if __name__ == "__main__":
    unittest.main()
