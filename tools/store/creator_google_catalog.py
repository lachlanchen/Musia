#!/usr/bin/env python3
"""Musia-only Google subscription drafts. No purchases or track releases."""

import argparse
import hashlib
import json
import re
from pathlib import Path
import sys
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from musia.creator.billing_providers import GoogleVerifier
from storelib import RUNTIME, now, private_dir, require, write_private

PACKAGE = "art.lazying.musia"
BASE = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"+PACKAGE
PLANS = {"creator": ("Creator", 9, 20), "studio": ("Studio", 29, 80)}


def catalog(key, apply=False):
    directory = private_dir(RUNTIME / "creator-google-catalog")
    with GoogleVerifier({"service_account_file":str(key)}).session() as session:
        def request(method, path, body=None, *, operation=None, missing=False):
            journal = directory / (hashlib.sha256(operation.encode()).hexdigest()+".json") if operation else None
            if journal:
                require(not journal.exists(), "Unknown/previous operation; reconcile exact product before retry")
                write_private(journal,{"state":"started", "at":now(), "path":path, "body":body})
            response = session.request(method,BASE+path,json=body,timeout=(10,45),allow_redirects=False)
            data = response.json() if response.content else {}
            if journal:
                write_private(journal,{"state":"accepted" if 200<=response.status_code<300 else "rejected",
                    "at":now(), "http":response.status_code, "response":data})
            if missing and response.status_code == 404:
                return None
            require(200<=response.status_code<300, f"Google catalog HTTP {response.status_code}; inspect private journal")
            return data
        report = []
        for tier,(name,units,renders) in PLANS.items():
            pid = "musia_"+tier
            existing = request("GET","/subscriptions/"+pid,missing=True)
            price = {"currencyCode":"USD", "units":str(units), "nanos":990000000}
            if not existing and apply:
                conversion = request("POST","/pricing:convertRegionPrices",{"price":price})
                version = conversion["regionVersion"]["version"]
                require(isinstance(version,str) and re.fullmatch(r"20[0-9]{2}/[0-9]{2}",version), "Unexpected regions version")
                body = {"packageName":PACKAGE, "productId":pid, "listings":[{
                    "languageCode":"en-US", "title":"Musia "+name,
                    "benefits":[f"{renders} song renders per calendar month", "Private or public creations"],
                    "description":f"{renders} song renders per UTC calendar month. Up to 3 minutes each. No rollover. Public listening and sharing remain free."}],
                    "basePlans":[{"basePlanId":"monthly", "autoRenewingBasePlanType":{
                        "billingPeriodDuration":"P1M", "gracePeriodDuration":"P3D",
                        "resubscribeState":"RESUBSCRIBE_STATE_INACTIVE"},
                        "regionalConfigs":[{"regionCode":"US", "newSubscriberAvailability":True,"price":price}]}]}
                request("POST","/subscriptions?"+urlencode({"productId":pid,"regionsVersion.version":version}),body,operation=pid+"-create-monthly")
                existing = request("GET","/subscriptions/"+pid)
            if existing:
                require(existing["packageName"]==PACKAGE and existing["productId"]==pid, "Product identity mismatch")
                plans = existing["basePlans"]
                require(len(plans)==1 and plans[0]["basePlanId"]=="monthly" and
                    plans[0]["autoRenewingBasePlanType"]["billingPeriodDuration"]=="P1M", "Unexpected existing plan")
                us = [r for r in plans[0]["regionalConfigs"] if r["regionCode"]=="US"]
                require(len(us)==1 and us[0]["price"]==price, "Existing price differs from approved target")
                report.append({"product":pid, "state":plans[0]["state"], "USD":f"{units}.99"})
            else:
                report.append({"product":pid, "action":"create_draft", "USD":f"{units}.99"})
        result = {"at":now(),"package":PACKAGE,"products":report,"salesEnabled":False,"releaseChanged":False}
        write_private(directory/"readback.json",result)
        return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--service-account-file",type=Path,required=True)
    p.add_argument("--apply-drafts",action="store_true")
    args = p.parse_args()
    print(json.dumps(catalog(args.service_account_file,args.apply_drafts),indent=2))
