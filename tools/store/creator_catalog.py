#!/usr/bin/env python3
"""Create Musia's approved subscription drafts, never submit or enable sales.

Separate from the beta uploader: that tool's formal-review guard stays intact.
Unknown mutation outcomes are journaled and must be reconciled by provider readback.
"""

import argparse
import hashlib
import json
import time
from urllib.parse import urlencode

import jwt
import requests

from storelib import Apple, GuardError, RUNTIME, config, now, private_dir, private_file, require, write_private

APP = "6816265930"
BUNDLE = "art.lazying.musia"
GROUP = "Musia generation"
PLANS = {"creator": ("Creator", "9.99", 20, 2), "studio": ("Studio", "29.99", 80, 1)}


def relationship(kind, identity):
    return {"data": {"type": kind, "id": identity}}


class Catalog:
    def __init__(self):
        self.cfg = config()
        self.read = Apple(self.cfg)
        require(self.read.app()["id"] == APP, "Wrong Apple app")
        self.directory = private_dir(RUNTIME / "creator-catalog")

    def create(self, kind, attributes, relationships, *, operation):
        require(kind in {"subscriptionGroups", "subscriptions", "subscriptionLocalizations",
                         "subscriptionGroupLocalizations", "subscriptionPrices", "subscriptionAvailabilities"}, "Unsupported catalog mutation")
        require(operation.startswith("musia-"), "Musia journal required")
        body = {"data": {"type": kind, "attributes": attributes, "relationships": relationships}}
        journal = self.directory / (hashlib.sha256(operation.encode()).hexdigest() + ".json")
        require(not journal.exists(), "Operation already attempted; read back before retry")
        token = jwt.encode({"iss": self.cfg["asc_issuer"], "iat": int(time.time()),
                            "exp": int(time.time())+300, "aud": "appstoreconnect-v1"},
                           private_file(self.cfg["asc_key_path"]).read_text(), algorithm="ES256",
                           headers={"kid": self.cfg["asc_key_id"]})
        write_private(journal, {"operation": operation, "state": "started", "at": now(), "request": body})
        with requests.Session() as session:
            session.trust_env = False
            response = session.post("https://api.appstoreconnect.apple.com/v1/"+kind, json=body,
                                    headers={"Authorization": "Bearer "+token}, timeout=(10,45), allow_redirects=False)
        result = response.json()
        write_private(journal, {"operation": operation, "state": "accepted" if response.status_code == 201 else "rejected",
                                "at": now(), "http": response.status_code, "response": result})
        require(response.status_code == 201, f"Apple catalog HTTP {response.status_code}; inspect protected journal")
        return result["data"]

    def run(self, apply=False):
        groups = self.read.rows(f"/v1/apps/{APP}/subscriptionGroups")
        require(len(groups) <= 1 and all(g["attributes"]["referenceName"] == GROUP for g in groups),
                "Unexpected existing Musia group; inspect before changing")
        if not groups and not apply:
            return {"app": APP, "action": "create_draft_group", "plans": PLANS, "salesEnabled": False}
        group = groups[0] if groups else self.create("subscriptionGroups", {"referenceName": GROUP},
                    {"app": relationship("apps",APP)}, operation="musia-generation-group")
        gid = group["id"]
        localizations = self.read.rows(f"/v1/subscriptionGroups/{gid}/subscriptionGroupLocalizations")
        if apply and not localizations:
            self.create("subscriptionGroupLocalizations", {"locale":"en-US", "name":"Musia generation"},
                        {"subscriptionGroup":relationship("subscriptionGroups",gid)}, operation="musia-group-en-US")
        products = self.read.rows(f"/v1/subscriptionGroups/{gid}/subscriptions")
        expected = {f"{BUNDLE}.{tier}.monthly" for tier in PLANS}
        require(all(p["attributes"]["productId"] in expected for p in products), "Unexpected subscription product")
        report = []
        for tier, (name, price, renders, level) in PLANS.items():
            pid = f"{BUNDLE}.{tier}.monthly"
            matches = [p for p in products if p["attributes"]["productId"] == pid]
            require(len(matches) <= 1, "Duplicate subscription")
            if not matches and not apply:
                report.append({"product":pid, "action":"create_draft"})
                continue
            product = matches[0] if matches else self.create("subscriptions",
                    {"name":"Musia "+name, "productId":pid, "subscriptionPeriod":"ONE_MONTH",
                     "familySharable":False, "groupLevel":level,
                     "reviewNote":f"{renders} song renders per UTC calendar month. Public listening and social features are free. Private creation is available on every tier. Test-only qualification; existing app reviews are unchanged."},
                    {"group":relationship("subscriptionGroups",gid)}, operation="musia-"+tier+"-monthly")
            sid = product["id"]
            require(product["attributes"]["subscriptionPeriod"] == "ONE_MONTH", "Existing period mismatch")
            try:
                availability = self.read.request("GET", f"/v1/subscriptions/{sid}/subscriptionAvailability")["data"]
            except GuardError as exc:
                if "HTTP 404;" not in str(exc):
                    raise
                availability = None
            if apply and not availability:
                # Initial sandbox storefront. Expand only after price/release qualification.
                self.create("subscriptionAvailabilities", {"availableInNewTerritories":False},
                    {"subscription":relationship("subscriptions",sid), "availableTerritories":{"data":[{"type":"territories","id":"USA"}]}},
                    operation="musia-"+tier+"-usa-availability")
            locales = self.read.rows(f"/v1/subscriptions/{sid}/subscriptionLocalizations")
            if apply and not locales:
                self.create("subscriptionLocalizations", {"locale":"en-US", "name":"Musia "+name,
                            "description":f"Create {renders} songs monthly. Keep private or share."},
                            {"subscription":relationship("subscriptions",sid)}, operation="musia-"+tier+"-en-US")
            points = self.read.rows(f"/v1/subscriptions/{sid}/pricePoints?"+urlencode({"filter[territory]":"USA", "limit":200}))
            match = [p for p in points if p["attributes"]["customerPrice"] == price]
            require(len(match) == 1, "Approved US price point not unique")
            prices = self.read.rows(f"/v1/subscriptions/{sid}/prices?"+urlencode({"filter[territory]":"USA", "include":"subscriptionPricePoint"}))
            if apply and not prices:
                self.create("subscriptionPrices", {"planType":"UPFRONT"}, {"subscription":relationship("subscriptions",sid),
                    "subscriptionPricePoint":relationship("subscriptionPricePoints",match[0]["id"]),
                    "territory":relationship("territories","USA")}, operation="musia-"+tier+"-usd-monthly-available-price")
            fresh = self.read.request("GET",f"/v1/subscriptions/{sid}")["data"]
            report.append({"product":pid, "id":sid, "state":fresh["attributes"]["state"], "approvedUSD":price,
                           "usPriceCount":len(self.read.rows(f"/v1/subscriptions/{sid}/prices?filter[territory]=USA"))})
        result = {"app":APP, "group":gid, "subscriptions":report, "salesEnabled":False, "reviewChanged":False, "at":now()}
        write_private(self.directory / "readback.json", result)
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply-drafts", action="store_true")
    args = parser.parse_args()
    print(json.dumps(Catalog().run(args.apply_drafts), indent=2))
