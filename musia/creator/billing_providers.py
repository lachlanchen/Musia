"""Online provider truth, normalized only after app and signature validation."""

from datetime import datetime
from pathlib import Path
import json
import re
from urllib.parse import quote

from .billing import APP_ID, BUNDLE, PRODUCTS, Snapshot, private_read
from .contracts import CreatorError


def product_tier(provider, product):
    for record in PRODUCTS:
        if record[provider+"ProductId"] == product:
            return record["tier"]
    raise CreatorError("billing_product_unrecognized", 403)


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError()
        return int(result.timestamp())
    except (AttributeError, ValueError):
        raise CreatorError("billing_provider_response_invalid", 503) from None


def plain(obj, name):
    value = getattr(obj, name, None)
    return getattr(value, "value", value)


class AppleVerifier:
    def __init__(self, config):
        self.config = config

    def signed_verifier(self, environment):
        from appstoreserverlibrary.signed_data_verifier import SignedDataVerifier
        roots = [Path(p).read_bytes() for p in self.config["root_certificate_files"]]
        return SignedDataVerifier(roots, True, environment, BUNDLE, APP_ID)

    def fetch(self, reference):
        if not re.fullmatch(r"[0-9]{1,64}", reference):
            raise CreatorError("billing_reference_invalid")
        from appstoreserverlibrary.api_client import AppStoreServerAPIClient, APIException
        from appstoreserverlibrary.models.Environment import Environment
        cfg = self.config
        environment = Environment.PRODUCTION if cfg["environment"] == "live" else Environment.SANDBOX
        verifier = self.signed_verifier(environment)
        client = AppStoreServerAPIClient(private_read(cfg["signing_key_file"]), cfg["key_id"], cfg["issuer_id"], BUNDLE, environment)
        try:
            try:
                info = client.get_transaction_info(reference)
                transaction = verifier.verify_and_decode_signed_transaction(info.signedTransactionInfo)
                if plain(transaction,"bundleId") != BUNDLE or plain(transaction,"environment") != environment.value:
                    raise CreatorError("billing_app_mismatch", 403)
                original = plain(transaction,"originalTransactionId")
                status = client.get_all_subscription_statuses(original)
            except APIException as exc:
                if cfg["environment"] == "live" and cfg.get("accept_sandbox") and exc.http_status_code == 404 and exc.raw_api_error in (4040005,4040010):
                    return AppleVerifier({**cfg,"environment":"test","accept_sandbox":False}).fetch(reference)
                raise
            matches = []
            for group in status.data or []:
                for last in group.lastTransactions or []:
                    if last.originalTransactionId != original:
                        continue
                    tx = verifier.verify_and_decode_signed_transaction(last.signedTransactionInfo)
                    renewal = verifier.verify_and_decode_renewal_info(last.signedRenewalInfo)
                    product = plain(tx,"productId")
                    if (plain(tx,"bundleId") != BUNDLE or plain(tx,"environment") != environment.value or
                        plain(renewal,"environment") != environment.value or
                        plain(tx,"type") != "Auto-Renewable Subscription" or
                        plain(tx,"inAppOwnershipType") != "PURCHASED" or plain(tx,"quantity") != 1 or
                        plain(tx,"originalTransactionId") != original or plain(renewal,"originalTransactionId") != original or
                        plain(renewal,"productId") != product):
                        raise CreatorError("billing_app_mismatch", 403)
                    state = {1:"active",2:"expired",3:"hold",4:"grace",5:"revoked"}.get(plain(last,"status"))
                    if state is None:
                        raise CreatorError("billing_provider_response_invalid", 503)
                    expiry = plain(renewal,"gracePeriodExpiresDate") if state == "grace" else plain(tx,"expiresDate")
                    if type(expiry) is not int:
                        raise CreatorError("billing_provider_response_invalid", 503)
                    if plain(tx,"revocationDate") is not None:
                        state = "revoked"
                    elif plain(tx,"isUpgraded") is True:
                        state = "expired"
                    elif state == "active" and plain(renewal,"autoRenewStatus") != 1:
                        state = "canceled"
                    matches.append(Snapshot("apple",str(original),product,product_tier("apple",product),state,
                                            expiry//1000,cfg["environment"],str(plain(tx,"appAccountToken") or "").lower()))
            if len(matches) != 1:
                raise CreatorError("billing_subscription_ambiguous", 409)
            return matches[0]
        except CreatorError:
            raise
        except Exception:
            raise CreatorError("billing_provider_unavailable", 503) from None

    def acknowledge(self, snapshot):
        pass


class GoogleVerifier:
    def __init__(self, config):
        self.config = config
        self.needs_ack = True

    def session(self):
        from google.oauth2.service_account import Credentials
        from google.auth.transport.requests import AuthorizedSession
        credentials = Credentials.from_service_account_info(json.loads(private_read(self.config["service_account_file"])),
                          scopes=["https://www.googleapis.com/auth/androidpublisher"])
        session = AuthorizedSession(credentials)
        session.trust_env = False
        return session

    def response(self, session, path):
        response = session.get("https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"+BUNDLE+path,
                               timeout=(5,20), allow_redirects=False)
        if response.status_code != 200 or len(response.content) > 1048576:
            raise CreatorError("billing_provider_unavailable", 503)
        value = response.json()
        if not isinstance(value, dict):
            raise CreatorError("billing_provider_response_invalid", 503)
        return value

    def fetch(self, reference):
        try:
            with self.session() as session:
                value = self.response(session,"/purchases/subscriptionsv2/tokens/"+quote(reference,safe=""))
                if value.get("kind") != "androidpublisher#subscriptionPurchaseV2" or len(value.get("lineItems",[])) != 1:
                    raise CreatorError("billing_provider_response_invalid", 503)
                environment = "test" if "testPurchase" in value else "live"
                if environment != self.config["environment"] and not (environment == "test" and self.config.get("accept_sandbox")):
                    raise CreatorError("billing_environment_mismatch", 403)
                line = value["lineItems"][0]
                product = line["productId"]
                tier = product_tier("google",product)
                offer = line.get("offerDetails",{})
                if offer.get("basePlanId") != "monthly" or offer.get("offerId"):
                    raise CreatorError("billing_product_unrecognized", 403)
                state = {"SUBSCRIPTION_STATE_PENDING":"pending","SUBSCRIPTION_STATE_ACTIVE":"active",
                         "SUBSCRIPTION_STATE_PAUSED":"hold","SUBSCRIPTION_STATE_IN_GRACE_PERIOD":"grace",
                         "SUBSCRIPTION_STATE_ON_HOLD":"hold","SUBSCRIPTION_STATE_CANCELED":"canceled",
                         "SUBSCRIPTION_STATE_EXPIRED":"expired","SUBSCRIPTION_STATE_PENDING_PURCHASE_CANCELED":"expired"}.get(value.get("subscriptionState"))
                if state is None:
                    raise CreatorError("billing_provider_response_invalid", 503)
                if state in ("active","grace","canceled"):
                    order_id = line.get("latestSuccessfulOrderId", "")
                    if not re.fullmatch(r"GPA\.[0-9.-]{1,100}",order_id):
                        raise CreatorError("billing_order_missing", 503)
                    order = self.response(session,"/orders/"+quote(order_id,safe=""))
                    if order.get("purchaseToken") != reference or order.get("orderId") != order_id or len(order.get("lineItems",[])) != 1 or order["lineItems"][0].get("productId") != product:
                        raise CreatorError("billing_order_mismatch", 403)
                    if order.get("state") in ("REFUNDED","CANCELED"):
                        state = "revoked"
                    elif order.get("state") not in ("PROCESSED","PARTIALLY_REFUNDED","PENDING_REFUND"):
                        state = "hold"
                acknowledgment = value.get("acknowledgementState")
                if acknowledgment not in ("ACKNOWLEDGEMENT_STATE_PENDING","ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED"):
                    raise CreatorError("billing_provider_response_invalid", 503)
                self.needs_ack = acknowledgment == "ACKNOWLEDGEMENT_STATE_PENDING"
                replaces = value.get("linkedPurchaseToken", "") if state in ("active","grace","canceled") else ""
                return Snapshot("google",reference,product,tier,state,timestamp(line["expiryTime"]) if line.get("expiryTime") else 0,
                                environment,value.get("externalAccountIdentifiers",{}).get("obfuscatedExternalAccountId",""),replaces)
        except CreatorError:
            raise
        except Exception:
            raise CreatorError("billing_provider_unavailable", 503) from None

    def acknowledge(self, snapshot):
        if not self.needs_ack or snapshot.state not in ("active","grace","canceled"):
            return
        try:
            with self.session() as session:
                response = session.post("https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"+BUNDLE+
                                        "/purchases/subscriptions/"+quote(snapshot.product,safe="")+"/tokens/"+
                                        quote(snapshot.reference,safe="")+":acknowledge",json={},timeout=(5,20),allow_redirects=False)
                if response.status_code not in (200,204):
                    raise ValueError()
        except Exception:
            raise CreatorError("billing_acknowledgement_pending", 503) from None
