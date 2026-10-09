"""Isolated creator acceptance tests. No issuer, GPU, store or payment contacted."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from musia.creator import media
from musia.creator.api import Settings, create_app
from musia.creator.contracts import AgentReply, Brief, Chat, CreatorError, Generate
from musia.creator.review import audio_digest, validate_audit
from musia.creator.store import Store
from musia.creator.worker import prepare


def brief():
    return Brief(title="Over the water", idea="Longing, then hope", lyrics="[Verse]\nOver the water\n[Chorus]\nI will find you",
                 caption="Warm piano, natural intimate singing, a hopeful memorable chorus", language="en")


def audit(checksum="a"*64):
    return {"audioSha256": checksum, "duration": 90, "listeningPassed": True, "inputCompared": True,
            "asrCompared": True, "gapsAndTailChecked": True, "contentApproved": True,
            "lines": [{"start": 3, "end": 8, "text": "Over the water", "language": "en"},
                      {"start": 80, "end": 86, "text": "I will find you", "language": "en"}]}


class Auth:
    revoked = False

    def providers(self):
        return {"password": True, "apple": False, "google": False, "github": False}

    def verify(self, session):
        if self.revoked:
            raise CreatorError("reconnect_account", 401)

    def sign_out(self, session):
        pass


class Producer:
    available = True

    def refine(self, request):
        return AgentReply(message="A warm chorus with room to breathe. Review it before rendering.", brief=brief())


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.clock = [1791504000]
        self.store = Store(self.root, clock=lambda: self.clock[0])
        self.token = self.store.signed_in("https://identity.example.test", "a", "Alice", "link-a")
        self.owner = self.store.session(self.token)["owner"]
        self.btoken = self.store.signed_in("https://identity.example.test", "b", "Bob", "link-b")
        self.other = self.store.session(self.btoken)["owner"]
        for owner in (self.owner, self.other):
            self.store.accept_terms(owner)
            self.store.redeem(owner, self.store.issue_invite(self.store.now()+300))

    def tearDown(self):
        self.temp.cleanup()

    def submit(self, key="one", owner=None, visibility="private"):
        return self.store.submit(owner or self.owner, key, Generate(brief=brief(), rights_confirmed=True, visibility=visibility))

    def reviewed(self, key="one", visibility="private", owner=None):
        job = self.submit(key, owner, visibility)
        self.store.approve_input(job["id"])
        lease = self.store.claim()
        self.assertEqual(job["id"], lease["id"])
        audio = self.root/"artifacts"/job["id"]/"song.wav"
        audio.parent.mkdir(parents=True)
        audio.write_bytes(b"RIFF-test-audio")
        checksum = audio_digest(audio)
        self.store.result(job["id"], lease["lease"], audio=str(audio), audio_hash=checksum, review="private-review")
        self.store.approve(job["id"], audit(checksum))
        return job["id"]


class LedgerTests(Base):
    def test_new_account_requires_terms_and_invitation_not_payment(self):
        token = self.store.signed_in("https://identity.example.test", "c", "C", "link-c")
        user = self.store.session(token)["owner"]
        with self.assertRaisesRegex(CreatorError, "accept_creator_terms"):
            self.submit(owner=user)
        self.store.accept_terms(user)
        with self.assertRaisesRegex(CreatorError, "creator_invitation_required"):
            self.submit(owner=user)
        self.assertEqual(self.store.profile(user)["usage"]["tier"], "free")

    def test_invite_single_use_and_no_tier_escalation(self):
        code = self.store.issue_invite(self.store.now()+30)
        token = self.store.signed_in("https://identity.example.test", "c", "C", "c")
        c = self.store.session(token)["owner"]
        self.store.redeem(c, code)
        self.store.redeem(c, code)
        token = self.store.signed_in("https://identity.example.test", "d", "D", "d")
        with self.assertRaisesRegex(CreatorError, "invitation_invalid"):
            self.store.redeem(self.store.session(token)["owner"], code)
        self.assertEqual(self.store.profile(c)["usage"]["tier"], "free")

    def test_duplicate_request_is_one_reservation_across_connections(self):
        def send(_):
            other = Store(self.root, clock=lambda: self.clock[0])
            return other.submit(self.owner, "same", Generate(brief=brief(), rights_confirmed=True))["id"]
        with ThreadPoolExecutor(8) as pool:
            ids = list(pool.map(send, range(12)))
        self.assertEqual(len(set(ids)), 1)
        self.assertEqual(self.store.profile(self.owner)["usage"]["used"], 1)

    def test_payload_changed_same_key_conflicts(self):
        self.submit()
        with self.assertRaisesRegex(CreatorError, "idempotency_conflict"):
            self.submit(visibility="public")

    def test_cross_account_key_independent(self):
        a, b = self.submit(), self.submit(owner=self.other)
        self.assertNotEqual(a["id"], b["id"])

    def test_concurrent_jobs_bounded(self):
        self.submit()
        with self.assertRaisesRegex(CreatorError, "finish_current_job"):
            self.submit("two")

    def test_monthly_quota_and_replay_when_exhausted(self):
        first = self.reviewed()
        self.reviewed("two")
        self.assertEqual(self.submit()["id"], first)
        with self.assertRaisesRegex(CreatorError, "monthly_generation_limit"):
            self.submit("three")
        self.clock[0] += 40*86400
        self.assertEqual(self.store.profile(self.owner)["usage"]["remaining"], 2)

    def test_cancel_refunds_once_and_preserves_idempotency(self):
        job = self.submit()["id"]
        self.store.cancel(self.owner, job)
        self.store.cancel(self.owner, job)
        self.assertEqual(self.store.profile(self.owner)["usage"]["used"], 0)
        self.assertEqual(self.submit()["state"], "cancelled")
        with self.assertRaisesRegex(CreatorError, "job_not_found"):
            self.store.cancel(self.other, job)

    def test_input_moderation_before_gpu(self):
        self.submit()
        self.assertIsNone(self.store.claim())

    def test_lease_claim_is_serial_and_not_reclaimed_implicitly(self):
        a, b = self.submit(), self.submit(owner=self.other)
        for job in (a,b):
            self.store.approve_input(job["id"])
        self.assertIsNotNone(self.store.claim())
        self.clock[0] += 10*86400
        self.assertIsNone(self.store.claim())

    def test_wrong_lease_rejected_and_failed_job_refunds(self):
        job = self.submit()["id"]
        self.store.approve_input(job)
        claim = self.store.claim()
        with self.assertRaisesRegex(CreatorError, "worker_lease_lost"):
            self.store.result(job, "fake", error="failed")
        self.store.result(job, claim["lease"], error="failed")
        self.assertEqual(self.store.profile(self.owner)["usage"]["remaining"], 2)

    def test_rejected_audio_refunds_and_stays_invisible(self):
        job = self.submit()["id"]
        self.store.approve_input(job)
        claim = self.store.claim()
        self.store.result(job, claim["lease"], audio="private", audio_hash="a"*64, review="r")
        self.store.reject(job)
        self.assertEqual(self.store.profile(self.owner)["usage"]["remaining"], 2)
        self.assertEqual(self.store.songs(), [])

    def test_private_and_pending_not_discoverable_even_with_id(self):
        song = self.reviewed(visibility="public")
        self.assertEqual(self.store.songs(), [])
        with self.assertRaisesRegex(CreatorError, "song_not_found"):
            self.store.song(song, self.other)
        self.assertTrue(self.store.song(song, self.owner)["mine"])
        self.store.moderate("song", song, True)
        self.assertEqual(len(self.store.songs()), 1)
        self.assertNotIn("brief", self.store.song(song))
        self.store.visibility(self.owner, song, "private")
        self.assertEqual(self.store.songs(), [])
        self.store.visibility(self.owner, song, "public")
        self.assertEqual(self.store.songs(), [])

    def test_free_social_and_private_saved_list(self):
        song = self.reviewed(visibility="public")
        self.store.moderate("song", song, True)
        before = self.store.profile(self.other)["usage"]
        for _ in range(2):
            self.store.react(self.other, song, "like", True)
            self.store.react(self.other, song, "save", True)
        self.assertEqual(self.store.song(song)["likes"], 1)
        self.assertFalse(self.store.song(song)["saved"])
        self.assertTrue(self.store.song(song, self.other)["saved"])
        self.assertEqual(self.store.profile(self.other)["usage"], before)
        self.assertEqual(len(self.store.songs(self.other, "saved")), 1)

    def test_comments_review_report_delete_and_block(self):
        song = self.reviewed(visibility="public")
        self.store.moderate("song", song, True)
        c = self.store.comment(self.other, song, "Beautiful chorus")
        self.assertEqual(self.store.comments(song), [])
        self.assertEqual(len(self.store.comments(song, self.other)), 1)
        self.store.moderate("comment", c, True)
        self.assertEqual(len(self.store.comments(song)), 1)
        self.store.report(self.other, song, "Please review attribution")
        self.store.block(self.other, self.owner, True)
        self.assertEqual(self.store.songs(self.other), [])
        self.assertEqual(self.store.comments(song, self.owner), [])
        self.store.block(self.other, self.owner, False)
        with self.assertRaisesRegex(CreatorError, "comment_not_found"):
            self.store.remove_comment(self.owner, c)
        self.store.remove_comment(self.other, c)
        self.assertEqual(self.store.comments(song), [])

    def test_cannot_make_someone_elses_song_public(self):
        song = self.reviewed(visibility="public")
        self.store.moderate("song", song, True)
        with self.assertRaisesRegex(CreatorError, "song_not_found"):
            self.store.visibility(self.other, song, "private")

    def test_suspended_account_cannot_interact_and_media_disappears(self):
        song = self.reviewed(visibility="public")
        self.store.moderate("song", song, True)
        self.store.suspend(self.owner)
        self.assertEqual(self.store.songs(), [])
        with self.assertRaises(CreatorError):
            self.store.session(self.token)

    def test_delete_cannot_resurrect_jobs_or_identity(self):
        job = self.submit()["id"]
        self.store.approve_input(job)
        claim = self.store.claim()
        self.store.delete_account(self.owner)
        with self.assertRaises(CreatorError):
            self.store.result(job, claim["lease"], audio="a", audio_hash="a"*64, review="r")
        with self.assertRaises(CreatorError):
            self.store.signed_in("https://identity.example.test", "a", "Alice", "new")

    def test_grant_expiry_does_not_reset_used_quota(self):
        self.reviewed()
        self.store.pilot_grant(self.owner, "studio", self.store.now()+30, "fixture only")
        self.assertEqual(self.store.profile(self.owner)["usage"]["remaining"], 79)
        self.clock[0] += 40
        self.assertEqual(self.store.profile(self.owner)["usage"]["remaining"], 1)

    def test_agent_turn_limit_and_failure_no_free_retry_loop(self):
        for _ in range(10):
            turn = self.store.start_turn(self.owner, "fixture")
            self.store.finish_turn(self.owner, turn, None)
        with self.assertRaisesRegex(CreatorError, "daily_limit_reached"):
            self.store.start_turn(self.owner, "fixture")

    def test_audio_changed_after_asr_requires_new_review(self):
        job = self.submit()["id"]
        self.store.approve_input(job)
        claim = self.store.claim()
        audio = self.root/"artifacts"/job/"song.wav"
        audio.parent.mkdir(parents=True)
        audio.write_bytes(b"first version")
        checksum = audio_digest(audio)
        self.store.result(job,claim["lease"],audio=str(audio),audio_hash=checksum,review="fixture")
        audio.write_bytes(b"replacement version")
        with self.assertRaisesRegex(ValueError,"Selected audio changed"):
            self.store.approve(job,audit(checksum))
        self.assertEqual(self.store.songs(self.owner,"mine"),[])

    def test_social_needs_no_generation_invite(self):
        song = self.reviewed(visibility="public")
        self.store.moderate("song",song,True)
        token = self.store.signed_in("https://identity.example.test","listener","Listener","listener-link")
        listener = self.store.session(token)["owner"]
        self.store.accept_terms(listener)
        self.store.react(listener,song,"like",True)
        self.store.react(listener,song,"save",True)
        self.store.comment(listener,song,"Lovely song")
        self.assertFalse(self.store.profile(listener)["invited"])
        self.assertEqual(self.store.profile(listener)["usage"]["used"],0)


class ApiTests(Base):
    def setUp(self):
        super().setUp()
        self.auth = Auth()
        self.config = Settings(origin="https://musia.example.test", directory=self.root, generation_enabled=True)
        self.client = TestClient(create_app(self.config, store=self.store, auth=self.auth, producer=Producer()), base_url=self.config.origin)
        self.client.cookies.set("__Secure-musia_creator", self.token, domain="musia.example.test", path="/creator")
        self.headers = {"Origin":self.config.origin,"X-Musia-Request":"1","Idempotency-Key":"one"}

    def tearDown(self):
        self.client.close()
        super().tearDown()

    def test_guest_library_and_plans_no_purchase_gate(self):
        self.client.cookies.clear()
        result = self.client.get("/creator/api/capabilities").json()
        self.assertFalse(result["salesEnabled"])
        self.assertEqual([p["renders"] for p in result["plans"]], [2,20,80])
        self.assertFalse(result["providers"]["apple"])
        self.assertEqual(self.client.get("/creator/api/songs").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/lessons").status_code, 200)

    def test_forged_identity_header_ignored(self):
        self.client.cookies.clear()
        r = self.client.post("/creator/api/jobs", json=Generate(brief=brief(), rights_confirmed=True).model_dump(), headers={**self.headers,"X-User-Id":self.owner,"X-Tier":"studio"})
        self.assertEqual(r.status_code, 401)

    def test_csrf_and_host_and_body_limit(self):
        self.assertEqual(self.client.post("/creator/api/terms",json={}).status_code,403)
        self.assertEqual(self.client.post("/creator/api/terms",json={},headers={**self.headers,"Origin":"https://evil.test"}).status_code,403)
        self.assertEqual(self.client.get("/creator/api/me",headers={"Host":"evil.test"}).status_code,400)
        self.assertEqual(self.client.post("/creator/api/agent",content='"'+'x'*50000+'"',headers={**self.headers,"Content-Type":"application/json"}).status_code,413)

    def test_no_client_tier_model_path_or_extra_worker_fields(self):
        data = Generate(brief=brief(), rights_confirmed=True).model_dump()
        for field in ("tier", "owner", "command", "output_path", "model"):
            response = self.client.post("/creator/api/jobs",json={**data,field:"fake"},headers=self.headers)
            self.assertEqual(response.status_code,422)
            self.assertEqual(response.json(),{"detail":"invalid_request"})

    def test_accepted_job_is_durable_no_inline_generation(self):
        result = self.client.post("/creator/api/jobs",json=Generate(brief=brief(),rights_confirmed=True).model_dump(),headers=self.headers)
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()["state"],"queued")
        self.assertIsNone(self.store.claim())
        self.assertFalse((self.root/"artifacts").exists())

    def test_revoked_central_identity_fails_closed(self):
        self.auth.revoked = True
        self.assertEqual(self.client.get("/creator/api/jobs").status_code,401)

    def test_stale_cookie_does_not_block_free_public_listening(self):
        self.auth.revoked = True
        self.assertEqual(self.client.get("/creator/api/songs").status_code,200)
        self.assertIsNone(self.client.get("/creator/api/me").json()["account"])

    def test_audio_acl_applies_to_ranges_and_after_unshare(self):
        song = self.reviewed(visibility="public")
        self.store.moderate("song",song,True)
        self.client.cookies.clear()
        url = f"/creator/api/songs/{song}/audio"
        response = self.client.get(url, headers={"Range":"bytes=0-3"})
        self.assertEqual(response.status_code,206)
        self.assertEqual(response.content,b"RIFF")
        self.assertIn("no-store",response.headers["cache-control"])
        self.store.visibility(self.owner,song,"private")
        self.assertEqual(self.client.get(url,headers={"Range":"bytes=0-3"}).status_code,404)

    def playback_fixture(self, visibility="private"):
        song = self.reviewed(visibility=visibility)
        source = self.root / "artifacts" / song / "song.wav"
        source.parent.chmod(0o700)
        playback = source.with_name("song.mp3")
        playback.write_bytes(b"ID3-playback-fixture-0123456789")
        playback.chmod(0o600)
        for target in ("musia.creator.media.prepare_playback", "subprocess.Popen"):
            guard = patch(target, side_effect=AssertionError("HTTP must not prepare media or spawn processes"))
            guard.start()
            self.addCleanup(guard.stop)
        return song, source, playback

    def assert_audio_response(self, response, payload, *, status=200, filename="song.mp3"):
        self.assertEqual(response.status_code, status)
        self.assertEqual(response.content, payload)
        self.assertEqual(response.headers["content-type"], "audio/mpeg" if filename.endswith(".mp3") else "audio/wav")
        self.assertEqual(response.headers["content-disposition"], f'inline; filename="{filename}"')
        self.assertEqual(response.headers["accept-ranges"], "bytes")
        self.assertIn("no-store", response.headers["cache-control"])
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")

    def test_playback_private_owner_mime_head_and_byte_ranges(self):
        song, source, playback = self.playback_fixture()
        url, payload = f"/creator/api/songs/{song}/audio", playback.read_bytes()
        with patch.object(media, "playback_path", return_value=playback) as lookup:
            response = self.client.get(url)
            self.assert_audio_response(response, payload)
            self.assertEqual(int(response.headers["content-length"]), len(payload))
            lookup.assert_called_once_with(source, audio_digest(source))
            response = self.client.head(url)
            self.assert_audio_response(response, b"")
            self.assertEqual(int(response.headers["content-length"]), len(payload))
            for byte_range, start, end in (("bytes=0-3", 0, 3),
                                           ("bytes=5-", 5, len(payload) - 1),
                                           ("bytes=-5", len(payload) - 5, len(payload) - 1)):
                with self.subTest(byte_range=byte_range):
                    response = self.client.get(url, headers={"Range": byte_range})
                    self.assert_audio_response(response, payload[start:end + 1], status=206)
                    self.assertEqual(response.headers["content-range"], f"bytes {start}-{end}/{len(payload)}")
                    self.assertEqual(int(response.headers["content-length"]), end - start + 1)
            response = self.client.get(url, headers={"Range": f"bytes={len(payload)}-"})
            self.assertEqual(response.status_code, 416)
            self.assertEqual(response.headers["content-range"], f"bytes */{len(payload)}")
            self.assertIn("no-store", response.headers["cache-control"])

    def test_playback_private_acl_precedes_lookup_for_get_head_and_range(self):
        song, source, playback = self.playback_fixture()
        url = f"/creator/api/songs/{song}/audio"
        self.client.cookies.clear()
        with patch.object(media, "playback_path", return_value=playback) as lookup:
            for token in (None, self.btoken, "invalid-session"):
                for method, extra in (("GET", {}), ("HEAD", {}), ("GET", {"Range": "bytes=0-3"})):
                    with self.subTest(token=token, method=method, extra=extra):
                        headers = {"Authorization": "Bearer " + token} if token else {}
                        response = self.client.request(method, url, headers={**headers, **extra})
                        self.assertEqual(response.status_code, 404)
                        self.assertIn("no-store", response.headers["cache-control"])
                        lookup.assert_not_called()
            response = self.client.get(url, headers={"Authorization": "Bearer " + self.token, "Range": "bytes=0-3"})
            self.assert_audio_response(response, playback.read_bytes()[:4], status=206)
            lookup.assert_called_once_with(source, audio_digest(source))

    def test_playback_public_requires_moderation_then_allows_guest_and_other_account(self):
        song, source, playback = self.playback_fixture(visibility="public")
        url, payload = f"/creator/api/songs/{song}/audio", playback.read_bytes()
        self.client.cookies.clear()
        with patch.object(media, "playback_path", return_value=playback) as lookup:
            for token in (None, self.btoken):
                headers = {"Authorization": "Bearer " + token} if token else {}
                self.assertEqual(self.client.get(url, headers={**headers, "Range": "bytes=0-3"}).status_code, 404)
            lookup.assert_not_called()
            self.store.moderate("song", song, True)
            for token in (None, self.btoken):
                headers = {"Authorization": "Bearer " + token} if token else {}
                for method, extra, status, body in (("GET", {}, 200, payload), ("HEAD", {}, 200, b""),
                                                    ("GET", {"Range": "bytes=0-3"}, 206, payload[:4])):
                    with self.subTest(token=token, method=method, extra=extra):
                        self.assert_audio_response(self.client.request(method, url, headers={**headers, **extra}),
                                                   body, status=status)
                        lookup.assert_called_with(source, audio_digest(source))

    def test_playback_unshare_revokes_guest_other_and_cached_ranges_but_not_owner(self):
        song, source, playback = self.playback_fixture(visibility="public")
        self.store.moderate("song", song, True)
        url = f"/creator/api/songs/{song}/audio"
        self.client.cookies.clear()
        with patch.object(media, "playback_path", return_value=playback) as lookup:
            response = self.client.get(url)
            self.assert_audio_response(response, playback.read_bytes())
            etag = response.headers["etag"]
            owner_headers = {**self.headers, "Authorization": "Bearer " + self.token}
            response = self.client.post(f"/creator/api/songs/{song}/visibility",
                                        json={"visibility": "private"}, headers=owner_headers)
            self.assertEqual(response.status_code, 200)
            lookup.reset_mock()
            for token in (None, self.btoken):
                headers = {"Authorization": "Bearer " + token} if token else {}
                for method, extra in (("GET", {}), ("HEAD", {}),
                                      ("GET", {"Range": "bytes=0-3", "If-Range": etag})):
                    with self.subTest(token=token, method=method, extra=extra):
                        response = self.client.request(method, url, headers={**headers, **extra})
                        self.assertEqual(response.status_code, 404)
                        self.assertIn("no-store", response.headers["cache-control"])
                        lookup.assert_not_called()
            self.assert_audio_response(self.client.get(url, headers={**owner_headers, "Range": "bytes=0-3"}),
                                       playback.read_bytes()[:4], status=206)
            lookup.assert_called_once_with(source, audio_digest(source))
            response = self.client.post(f"/creator/api/songs/{song}/visibility",
                                        json={"visibility": "public"}, headers=owner_headers)
            self.assertEqual(response.status_code, 200)
            lookup.reset_mock()
            self.assertEqual(self.client.get(url, headers={"Range": "bytes=0-3"}).status_code, 404)
            lookup.assert_not_called()

    def test_playback_invalid_manifest_uses_wav_mime_head_and_ranges_without_repair(self):
        song, source, playback = self.playback_fixture()
        manifest = source.with_name("playback.json")
        manifest.write_bytes(b'{"schema":')
        manifest.chmod(0o600)
        before = [path.read_bytes() for path in (source, playback, manifest)]
        url, payload = f"/creator/api/songs/{song}/audio", source.read_bytes()
        with patch.object(media, "playback_path", wraps=media.playback_path) as lookup:
            response = self.client.get(url)
            self.assert_audio_response(response, payload, filename="song.wav")
            self.assertEqual(int(response.headers["content-length"]), len(payload))
            response = self.client.head(url)
            self.assert_audio_response(response, b"", filename="song.wav")
            self.assertEqual(int(response.headers["content-length"]), len(payload))
            response = self.client.get(url, headers={"Range": "bytes=0-3"})
            self.assert_audio_response(response, payload[:4], status=206, filename="song.wav")
            self.assertEqual(response.headers["content-range"], f"bytes 0-3/{len(payload)}")
            self.assertEqual(int(response.headers["content-length"]), 4)
            self.assertEqual(lookup.call_count, 3)
            lookup.assert_called_with(source, audio_digest(source))
            self.client.cookies.clear()
            lookup.reset_mock()
            self.assertEqual(self.client.get(url, headers={"Range": "bytes=0-3"}).status_code, 404)
            lookup.assert_not_called()
        self.assertEqual([path.read_bytes() for path in (source, playback, manifest)], before)
        self.assertEqual(set(source.parent.iterdir()), {source, playback, manifest})

    def test_audio_not_exposed_before_approval(self):
        job = self.submit()["id"]
        self.assertEqual(self.client.get(f"/creator/api/songs/{job}/audio").status_code,404)

    def test_creator_static_csp_and_existing_studio_not_mounted(self):
        response = self.client.get("/creator/")
        self.assertEqual(response.status_code,200)
        self.assertIn("frame-ancestors 'none'",response.headers["content-security-policy"])
        self.assertEqual(self.client.get("/creator/app.js").status_code,200)
        for path in ("/creator/api/exec","/creator/.env","/creator/../../.env","/studio"):
            self.assertEqual(self.client.get(path).status_code,404)

    def test_agent_returns_bounded_brief_not_job(self):
        result = self.client.post("/creator/api/agent",json={"message":"A hopeful song"},headers=self.headers)
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()["brief"]["language"],"en")
        self.assertEqual(self.store.jobs(self.owner),[])

    def test_missing_capabilities_disabled_no_fake_login(self):
        client = TestClient(create_app(Settings(directory=self.root),store=self.store),base_url="http://127.0.0.1:8796")
        with client:
            data = client.get("/creator/api/capabilities").json()
            self.assertFalse(data["generation"])
            self.assertFalse(data["login"])
            self.assertEqual(data["providers"],{})


class ContractTests(unittest.TestCase):
    def test_partial_draft_preserves_user_lyrics_for_agent(self):
        request = Chat.model_validate({"message":"Keep these source lines", "brief":{"lyrics":"天蓝蓝\n海蓝蓝"}})
        self.assertEqual(request.brief.lyrics, "天蓝蓝\n海蓝蓝")
        self.assertEqual(request.brief.title, "")

    def test_bounded_brief_and_rights(self):
        for change in ({"duration":True},{"duration":181},{"lyrics":""},{"bpm":300},{"key":"x; rm -rf"},{"reference_audio":"/etc/passwd"}):
            with self.assertRaises(ValidationError):
                Brief.model_validate({**brief().model_dump(),**change})
        for value in (False, 1, "true"):
            with self.assertRaises(ValidationError):
                Generate(brief=brief(),rights_confirmed=value)

    def test_audit_requires_cross_validation_tail_and_digest(self):
        validate_audit(audit(),"a"*64)
        for key in ("listeningPassed","inputCompared","asrCompared","gapsAndTailChecked","contentApproved"):
            with self.assertRaises(ValueError):
                validate_audit({**audit(),key:False},"a"*64)
        with self.assertRaises(ValueError):
            validate_audit(audit(),"b"*64)

    def test_audit_rejects_fabricated_instrumental_and_bad_time(self):
        for line in ({"start":0,"end":4,"text":"♪","language":"en"},
                     {"start":4,"end":2,"text":"x","language":"en"},
                     {"start":float('nan'),"end":4,"text":"x","language":"en"}):
            with self.assertRaises(ValueError):
                validate_audit({**audit(),"lines":[line]},"a"*64)

    def test_worker_has_fixed_argv_and_user_lyrics_are_only_file_content(self):
        with tempfile.TemporaryDirectory() as temp:
            b = brief().model_copy(update={"lyrics":"$(touch /tmp/not-permitted)\n'; rm -rf'"})
            folder=Path(temp)/"job"
            command=prepare({"brief":b.model_dump_json(),"id":"a"*32},folder)
            self.assertNotIn(b.lyrics,command)
            self.assertEqual((folder/"lyrics.txt").read_text(),b.lyrics)
            self.assertIn("run_ace_candidate_sweep.py",command[1])


if __name__ == "__main__":
    unittest.main()
