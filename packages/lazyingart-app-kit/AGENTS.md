# Shared App Kit Rules

- This is a candidate client/contract package, not the central account service.
- Company owns the account policy; the active EchoMind owner owns the issuer.
  Consult `docs/lazyingart-app-framework.md` from the Musia repository root.
- Keep tests portable and fixtures synthetic. No production credentials,
  issuer guesses, account databases or raw cross-project session transcripts.
- Tests are not live provider evidence. Do not enable login or alter a store
  review candidate because mocked exchanges pass.
- New native integrations remain SwiftUI/Kotlin; no JS runtime requirement.
- Keep issuer + subject identity, app entitlement, purchases, credits, private
  content, generation budget and publication consent separate.
- Refresh is one-use: never retry a possibly consumed refresh credential.
  Preserve local drafts on logout, expiry, cancellation and outage.
- Require durable atomic stores from adopters. Test in-memory stores are not
  deployment defaults. Do not add a fallback that silently uses them.
- Run package tests, Musia adoption tests and existing learning API tests after
  changes. Hand off sibling integration to its current owner; no bulk migration.
