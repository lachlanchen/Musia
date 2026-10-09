"""Optional central-account adapter. Provider credentials never reach Musia clients."""

from pathlib import Path

from .contracts import CreatorError


class CentralAuth:
    def __init__(self, directory: Path, origin: str):
        # Install the reviewed LazyingArtLinkPrivate package in the service env.
        from lazyingart_link import Client, LinkStore, LinkError
        from lazyingart_link.onboard import load_private

        config, key = load_private(directory)
        if config.redirect_uri != origin + "/creator/auth/callback" or config.client_id != "musia-server" or config.audience != "musia-service":
            raise ValueError("Musia requires its own registered client, audience and exact callback")
        self.client, self.error = Client(config), LinkError
        self.vault = LinkStore(directory / "sessions.sqlite", config, key)

    def providers(self):
        if not self.client.config.enabled:
            return {}
        try:
            return self.client.discovery()["providers"]
        except self.error:
            return {}

    def begin(self, binding):
        try:
            return self.client.authorize(self.vault, binding)
        except self.error:
            raise CreatorError("sign_in_unavailable", 503) from None

    def complete(self, url, binding, store):
        try:
            tokens, identity = self.client.complete(self.vault, url, binding)
            link = self.vault.save_session(tokens, identity)
            try:
                return store.signed_in(identity.issuer, identity.subject, identity.display_name, link)
            except CreatorError:
                self.vault.sign_out(self.client, link, expected_subject=identity.subject)
                raise
        except self.error:
            raise CreatorError("sign_in_failed", 401) from None

    def verify(self, session):
        user, link = session["user"], session["link_id"]
        try:
            try:
                tokens, _ = self.vault.session(link, expected_subject=user["subject"])
            except self.error as exc:
                if exc.code != "session_refresh_required":
                    raise
                tokens, _ = self.vault.refresh(self.client, link, expected_subject=user["subject"])
            identity = self.client.introspect(tokens.access_token, expected_subject=user["subject"])
            if identity is None or identity.issuer != user["issuer"]:
                raise CreatorError("reconnect_account", 401)
        except self.error:
            raise CreatorError("reconnect_account", 401) from None

    def sign_out(self, session):
        try:
            self.vault.sign_out(self.client, session["link_id"], expected_subject=session["user"]["subject"])
        except self.error:
            # The SDK durably revokes locally before any remote request.
            # Its revocation_pending record remains for operator reconciliation.
            pass
