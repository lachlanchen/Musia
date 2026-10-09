import base64
import contextlib
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import musia_store as m
from build_native import WATCH_BUNDLE
from storelib import GuardError


class API:
    def __init__(self, existing=False):
        self.existing = existing
        self.posts = []
    def inventory(self):
        return {"bundle_ids":[{"id":"main", "attributes":{"identifier":m.BUNDLE}}], "apps":[{"id":"app"}]}
    def rows(self, path):
        if path.startswith("/v1/bundleIds?"):
            suffix = ".other" if not self.existing else ""
            return [{"id":"watch", "attributes":{"identifier":WATCH_BUNDLE + suffix}}]
        return [{"id":"profile", "attributes":{"name":"Musia Watch App Store", "profileType":"IOS_APP_STORE", "profileState":"ACTIVE"}}] if self.existing else []
    def request(self, method, path, body=None, operation=None):
        if method == "POST": self.posts.append((path, body, operation))
        if path.startswith("/v1/certificates/"):
            return {"data":{"id":"cert", "attributes":{"certificateType":"DISTRIBUTION", "certificateContent":base64.b64encode(b"certificate").decode()}}}
        if path == "/v1/bundleIds":
            return {"data":{"id":"watch", "attributes":body["data"]["attributes"]}}
        return {"data":{"id":"profile", "attributes":{"profileContent":base64.b64encode(b"profile").decode()}}}


class WatchSetupTests(unittest.TestCase):
    def run_setup(self, api, confirm):
        cfg = {"apple_certificate_id":"cert", "apple_certificate_sha1":hashlib.sha1(b"certificate").hexdigest().upper()}
        with tempfile.TemporaryDirectory() as directory, patch.object(m,"RUNTIME",Path(directory)), \
             patch.object(m,"config",return_value=cfg), patch.object(m,"Apple",return_value=api), \
             patch.object(m,"lock",return_value=contextlib.nullcontext()), \
             patch.object(m,"decode_profile",return_value={"UUID":"watch-profile"}), \
             patch.object(m,"check_profile",side_effect=lambda p,c,b: p if b == WATCH_BUNDLE else self.fail("Wrong profile identity")):
            return m.apple_setup(confirm, watch=True)
    def test_plan_does_not_mutate_and_ignores_prefix_sibling(self):
        api = API()
        result = self.run_setup(api, False)
        self.assertTrue(result["register_bundle"])
        self.assertFalse(api.posts)
    def test_watch_setup_uses_existing_certificate_and_no_new_app_record(self):
        api = API()
        result = self.run_setup(api, True)
        self.assertEqual(result["bundle_id"], WATCH_BUNDLE)
        self.assertFalse(result["app_record_created"])
        self.assertEqual([x[0] for x in api.posts], ["/v1/bundleIds", "/v1/profiles"])
        self.assertEqual(api.posts[1][1]["data"]["relationships"]["certificates"]["data"], [{"type":"certificates", "id":"cert"}])
        self.assertTrue(all("musia-watch" in x[2] for x in api.posts))
    def test_existing_watch_profile_is_reused(self):
        api = API(existing=True)
        self.run_setup(api, True)
        self.assertFalse(api.posts)
    def test_companion_must_exist(self):
        api = API()
        api.inventory = lambda: {"bundle_ids":[], "apps":[]}
        with self.assertRaises(GuardError): self.run_setup(api, True)
