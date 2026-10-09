#!/usr/bin/env python3
"""Musia-only Google catalog. Default read-only; draft creation stays separate.

--activate-base-plans activates only the approved existing US monthly plans.
Activation makes the catalog available in Play, not a sandbox-only product.
It requires protected Google test configuration with BOTH checkout gates closed.
It does not qualify license testers, authorize purchases, or change app gates.
An uncertain activation is reconciled on a later invocation, never retried.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path
import sys
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from musia.creator.billing_providers import GoogleVerifier
from musia.creator.billing import APP_ID
from storelib import GuardError, RUNTIME, lock, now, private_dir, private_file, read_json, require, write_private

PACKAGE = "art.lazying.musia"
BASE = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"+PACKAGE
PLANS = {"creator": ("Creator", 9, 20), "studio": ("Studio", 29, 80)}


def billing_guard(key, billing_config):
    require(billing_config is not None, "Activation requires --billing-config")
    path = private_file(Path(billing_config).expanduser().absolute())
    raw = path.read_bytes()
    value = json.loads(raw)
    require(value.get("schema") == 1 and isinstance(value.get("providers"), dict), "Invalid billing configuration")
    google = value["providers"].get("google", {})
    require(google.get("bundle_id") == PACKAGE and google.get("app_id") == APP_ID,
            "Billing configuration must explicitly identify Musia")
    require(google.get("environment") == "test" and google.get("sales_enabled") is False
            and google.get("test_sales_enabled") is False, "Both Google checkout gates must be explicitly false in test environment")
    key = private_file(Path(key).expanduser().absolute())
    require(google.get("service_account_file") == str(key), "Use the protected billing configuration's Google key")
    return hashlib.sha256(raw).hexdigest()


def activation_path(pid):
    require(pid in {"musia_" + tier for tier in PLANS}, "Unapproved subscription")
    return f"/subscriptions/{pid}/basePlans/monthly:activate"


def activation_journal(directory, pid):
    operation = PACKAGE + activation_path(pid)
    return directory / (hashlib.sha256(operation.encode()).hexdigest() + ".json")


def activation_request(session, method, path):
    require(method == "GET" or (method == "POST" and path in {activation_path("musia_" + t) for t in PLANS}),
            "Only exact base-plan activation writes are allowed")
    try:
        response = session.request(method, BASE + path, timeout=(10, 45), allow_redirects=False,
                                   **({"json": {}} if method == "POST" else {}))
        # Play returns 204 for empty offer lists. Never accept this for a mutation
        # or a subscription resource, where a JSON readback is required.
        offer_paths = {f"/subscriptions/musia_{t}/basePlans/monthly/offers" for t in PLANS}
        if method == "GET" and path.partition("?")[0] in offer_paths and response.status_code == 204:
            require(response.content == b"", "Unexpected body on empty offers response")
            return {"subscriptionOffers": []}
        require(response.status_code == 200, "Google activation/readback HTTP failure; reconcile before retry")
        require(bool(response.content) and len(response.content) <= 1048576, "Missing/oversized Google response")
        value = response.json()
        require(isinstance(value, dict) and "error" not in value, "Invalid Google response object")
        return value
    except Exception:
        raise GuardError("Google activation/readback response unconfirmed; inspect journal, never blindly retry") from None


def approved_plan(product, pid):
    units = PLANS[pid.removeprefix("musia_")][1]
    require(product.get("packageName") == PACKAGE and product.get("productId") == pid
            and product.get("archived", False) is False, "Wrong/archived subscription")
    plans = product.get("basePlans")
    require(isinstance(plans, list) and len(plans) == 1, "Expected exactly one base plan")
    plan = plans[0]
    require(plan.get("basePlanId") == "monthly" and plan.get("state") in {"DRAFT", "ACTIVE"}, "Unexpected base plan/state")
    auto = plan.get("autoRenewingBasePlanType", {})
    require(auto.get("billingPeriodDuration") == "P1M" and "prepaidBasePlanType" not in plan
            and "installmentsBasePlanType" not in plan and not auto.get("legacyCompatibleSubscriptionOfferId"),
            "Expected monthly auto-renewing base plan without legacy offer")
    regions = plan.get("regionalConfigs")
    price = {"currencyCode": "USD", "units": str(units), "nanos": 990000000}
    require(isinstance(regions, list) and len(regions) == 1 and regions[0].get("regionCode") == "US"
            and regions[0].get("newSubscriberAvailability") is True and regions[0].get("price") == price,
            "Plan must be US-only at the exact approved price")
    other = plan.get("otherRegionsConfig", {})
    require(isinstance(other, dict) and other.get("newSubscriberAvailability", False) is False,
            "Future-region availability must be off")
    return plan


def read_activation_catalog(session):
    products = {"musia_" + t: activation_request(session, "GET", "/subscriptions/musia_" + t) for t in PLANS}
    for pid, product in products.items():
        approved_plan(product, pid)
        seen, token = set(), None
        for _ in range(20):
            query = {"pageSize": 1000, **({"pageToken": token} if token else {})}
            offers = activation_request(session, "GET", f"/subscriptions/{pid}/basePlans/monthly/offers?" + urlencode(query))
            require(set(offers) <= {"subscriptionOffers", "nextPageToken"}
                    and offers.get("subscriptionOffers", []) == [], "Existing/invalid offers; activation refused")
            token = offers.get("nextPageToken", "")
            require(isinstance(token, str), "Invalid offer pagination")
            if not token:
                break
            require(token not in seen, "Repeated offer pagination token")
            seen.add(token)
        else:
            raise GuardError("Offer pagination incomplete; no activation")
    return products


def activate_base_plans(key, billing_config):
    key = Path(key).expanduser().absolute()
    with lock("creator-google-catalog-activation"):
        config_sha = billing_guard(key, billing_config)
        directory = private_dir(RUNTIME / "creator-google-catalog")
        with GoogleVerifier({"service_account_file": str(key)}).session() as session:
            # Disable AuthorizedSession's automatic 401 replay as well as HTTP retries.
            require(hasattr(session, "_max_refresh_attempts"), "Unsupported Google retry policy")
            session._max_refresh_attempts = 0
            session.trust_env = False
            from requests.adapters import HTTPAdapter
            session.mount("https://", HTTPAdapter(max_retries=0))
            products = read_activation_catalog(session)
            previous = {}
            for pid, product in products.items():
                journal = activation_journal(directory, pid)
                if journal.exists():
                    record = read_json(private_file(journal))
                    require(record.get("package") == PACKAGE and record.get("path") == activation_path(pid)
                            and record.get("body") == {} and record.get("state") in {"started", "unknown", "active"},
                            "Activation journal mismatch; manual reconciliation required")
                    require(approved_plan(product, pid)["state"] == "ACTIVE",
                            "Previous activation still unconfirmed; readback only, no POST retry")
                    previous[pid] = record
            report = []
            for pid, product in products.items():
                require(billing_guard(key, billing_config) == config_sha, "Billing configuration changed; no further activation")
                journal = activation_journal(directory, pid)
                if approved_plan(product, pid)["state"] == "ACTIVE":
                    if pid in previous:
                        previous[pid].update(state="active", readback_at=now(), readback=product)
                        write_private(journal, previous[pid])
                    report.append({"product": pid, "state": "ACTIVE", "action": "verified_skipped"})
                    continue
                require(not journal.exists(), "Activation already attempted; reconcile without retry")
                record = {"state": "started", "at": now(), "package": PACKAGE, "path": activation_path(pid),
                          "body": {}, "billing_config_sha256": config_sha, "before": product}
                write_private(journal, record)
                try:
                    response = activation_request(session, "POST", activation_path(pid))
                    require(approved_plan(response, pid)["state"] == "ACTIVE", "Activation response is not ACTIVE")
                    fresh = read_activation_catalog(session)
                    require(approved_plan(fresh[pid], pid)["state"] == "ACTIVE", "ACTIVE readback missing")
                    require(billing_guard(key, billing_config) == config_sha, "Billing configuration changed during activation")
                except Exception:
                    record.update(state="unknown", at=now())
                    write_private(journal, record)
                    raise GuardError("Activation outcome unconfirmed; rerun for readback only, never remove journals to retry") from None
                record.update(state="active", readback_at=now(), readback=fresh[pid])
                write_private(journal, record)
                # Carry fresh validation of BOTH products/offers into the next operation.
                products.update(fresh)
                report.append({"product": pid, "state": "ACTIVE", "action": "activated_verified"})
            require(billing_guard(key, billing_config) == config_sha, "Billing configuration changed during readback")
            require(all(approved_plan(product, pid)["state"] == "ACTIVE" for pid, product in products.items()),
                    "Both approved plans must remain ACTIVE in final readback")
            result = {"at": now(), "package": PACKAGE, "products": report, "salesEnabled": False,
                      "testSalesEnabled": False, "licenseTestingVerified": False, "purchasesAuthorized": False,
                      "releaseChanged": False}
            write_private(directory / "activation-readback.json", result)
            return result


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


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--service-account-file",type=Path,required=True)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--apply-drafts",action="store_true")
    mode.add_argument("--activate-base-plans",action="store_true")
    p.add_argument("--billing-config",type=Path,help="Protected billing JSON; required only for activation")
    args = p.parse_args(argv)
    try:
        require(args.activate_base_plans or args.billing_config is None, "--billing-config requires --activate-base-plans")
        result = activate_base_plans(args.service_account_file, args.billing_config) if args.activate_base_plans else catalog(args.service_account_file,args.apply_drafts)
        print(json.dumps(result,indent=2))
        return 0
    except (GuardError, OSError, ValueError, KeyError, TypeError, ImportError, AttributeError) as error:
        print(str(error) if isinstance(error, GuardError) else "Invalid local/provider input; no retry authorized", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
