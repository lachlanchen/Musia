"""One owned tab on the existing store browser; no edit transaction for inventory."""
import json
import re
import time
import urllib.request

from storelib import BUNDLE, DEVELOPER, RUNTIME, config, now, require, snapshot_artifact, write_private


class OwnedTab:
    def __init__(self, cfg):
        import websocket
        port = cfg.get("store_cdp_port")
        require(isinstance(port, int) and 1024 <= port <= 65535, "Configure the existing loopback store CDP port")
        self.base = f"http://127.0.0.1:{port}"
        request = urllib.request.Request(self.base + "/json/new?about:blank", method="PUT")
        self.page = json.load(urllib.request.urlopen(request, timeout=10))
        self.seq = 0
        try:
            self.ws = websocket.create_connection(self.page["webSocketDebuggerUrl"], suppress_origin=True, timeout=25)
        except Exception:
            urllib.request.urlopen(self.base + "/json/close/" + self.page["id"], timeout=10).read()
            raise

    def call(self, method, **params):
        self.seq += 1
        self.ws.send(json.dumps({"id": self.seq, "method": method, "params": params}))
        while True:
            result = json.loads(self.ws.recv())
            if result.get("id") == self.seq:
                require("error" not in result, "CDP operation failed; no provider retry")
                return result.get("result", {})

    def evaluate(self, expression):
        result = self.call("Runtime.evaluate", expression=expression, returnByValue=True)
        require("exceptionDetails" not in result, "Store page inspection failed")
        return result.get("result", {}).get("value")

    def view(self):
        return self.evaluate("({url:location.href,text:document.body?.innerText ?? ''})")

    def close(self):
        self.ws.close()
        urllib.request.urlopen(self.base + "/json/close/" + self.page["id"], timeout=10).read()


def inventory():
    cfg = config()
    tab = OwnedTab(cfg)
    try:
        expected = f"https://play.google.com/console/u/0/developers/{DEVELOPER}/app-list"
        tab.call("Page.navigate", url=expected)
        for _ in range(60):
            view = tab.view()
            page = re.search(r"(\d+)\s*[-\u2013]\s*(\d+)\s+of\s+(\d+)", view["text"])
            if view["url"] == expected and page and f"Account ID: {DEVELOPER}" in view["text"]:
                break
            time.sleep(1)
        require(view["url"] == expected and f"Account ID: {DEVELOPER}" in view["text"], "Wrong Play account or login required")
        require(page and int(page[1]) == 1 and page[2] == page[3], "App list incomplete; inspect further pages manually")
        matches = BUNDLE in view["text"] or bool(re.search(r"(?im)^Musia(?:\s*[:\-].*)?$", view["text"]))
        receipt = {"at": now(), "account_id": DEVELOPER, "bundle_id": BUNDLE, "complete": True,
                   "app_count": int(page[3]), "musia_present": matches, "page": view}
        write_private(RUNTIME / "play-inventory.json", receipt)
        return {k: v for k, v in receipt.items() if k != "page"}
    finally:
        tab.close()


def upload(build, confirm=False):
    cfg = config()
    app = cfg.get("google_app_id")
    url = cfg.get("play_upload_url", "")
    prefix = f"https://play.google.com/console/u/0/developers/{DEVELOPER}/app/{app}/"
    require(app and app.isdigit() and url.startswith(prefix) and "prepare" in url
            and "production" not in url, "Configure Musia's observed internal prepare URL, never another app's URL")
    tab = OwnedTab(cfg)
    dispatched = False
    try:
        tab.call("Page.navigate", url=url)
        for _ in range(45):
            view = tab.view()
            if BUNDLE in view["text"] and "Internal testing" in view["text"]:
                break
            time.sleep(1)
        require(view["url"] == url and BUNDLE in view["text"] and "Internal testing" in view["text"],
                "Cannot prove this is Musia internal testing; no upload")
        selector = 'input[type="file"][accept*=".aab"]'
        count = tab.evaluate(f"document.querySelectorAll({json.dumps(selector)}).length")
        require(count == 1, "Unambiguous AAB upload control not found")
        if not confirm:
            return {"state": "upload_plan_only", "app_id": app, "artifact_sha256": build["artifact_sha256"]}
        build = snapshot_artifact(build)
        journal = RUNTIME / "operations" / ("play-upload-" + build["artifact_sha256"] + ".json")
        require(not journal.exists(), "Upload already attempted; read back bundle library before retry")
        write_private(journal, {"state": "started", "at": now(), "bundle_id": BUNDLE, "sha256": build["artifact_sha256"]})
        root = tab.call("DOM.getDocument")["root"]["nodeId"]
        node = tab.call("DOM.querySelector", nodeId=root, selector=selector)["nodeId"]
        dispatched = True
        tab.call("DOM.setFileInputFiles", nodeId=node, files=[build["artifact"]])
        time.sleep(5)
        write_private(journal, {"state": "upload_dispatched_readback_required", "at": now(),
                                "sha256": build["artifact_sha256"], "page": tab.view(), "owned_tab": tab.page["id"]})
        return {"state": "upload_dispatched_readback_required", "published": False,
                "note": "Owned upload tab retained so upload can finish. Reconcile processing, then close that exact tab. No Publish or review action."}
    finally:
        if dispatched:
            # Closing a tab immediately after selecting the AAB can abort its upload.
            write_private(RUNTIME / "play-upload-tab.json", {"id": tab.page["id"], "at": now(),
                          "reason": "Upload may be in flight; observe completion before closing this owned tab"})
            tab.ws.close()
        else:
            tab.close()


def test_access(build):
    cfg = config()
    app = cfg.get("google_app_id")
    prefix = f"https://play.google.com/console/u/0/developers/{DEVELOPER}/app/{app}/tracks/"
    internal = cfg.get("play_internal_url", "")
    testers = cfg.get("play_testers_url", "")
    opt_in = cfg.get("play_opt_in_url", "")
    require(app and app.isdigit() and all(u.startswith(prefix) and "production" not in u and "prepare" not in u
                                       for u in (internal, testers)), "Configure observed Musia internal/tester URLs")
    require(re.fullmatch(r"https://play\.google\.com/apps/internaltest/\d+", opt_in), "Invalid internal opt-in URL")
    recipient = cfg.get("self_tester_email", "")
    require("@" in recipient and not any(c in recipient for c in "\r\n"), "Private recipient missing")
    tab = OwnedTab(cfg)
    try:
        tab.call("Page.navigate", url=internal)
        for _ in range(60):
            view = tab.view()
            if "Available to internal testers" in view["text"]:
                break
            time.sleep(1)
        version = re.escape(str(build["build_number"])) + r"\s*\(" + re.escape(build["version"]) + r"\)"
        require(view["url"] == internal and BUNDLE in view["text"] and "Internal testing" in view["text"]
                and "Available to internal testers" in view["text"] and re.search(version, view["text"]),
                "Exact Musia internal release not proven available")
        release_view = view
        tab.call("Page.navigate", url=testers)
        for _ in range(45):
            view = tab.view()
            links = tab.evaluate("[...document.querySelectorAll('a[href]')].map(a=>a.href)")
            if opt_in in links and recipient.casefold() in view["text"].casefold():
                break
            time.sleep(1)
        require(view["url"] == testers and opt_in in links and recipient.casefold() in view["text"].casefold(),
                "Exact opt-in URL and owner tester access not visible; inspect Console without guessing")
        receipt = {"at": now(), "bundle_id": BUNDLE, "build_number": build["build_number"],
                   "sha256": build["artifact_sha256"], "release": release_view, "testers": view, "opt_in": opt_in}
        write_private(RUNTIME / "play-test-access.json", receipt)
        return opt_in
    finally:
        tab.close()
