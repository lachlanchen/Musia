# Shared App Kit: Owner Handoff

Source: Musia, 2026-09-27. **Candidate only; no login or deployment enabled.**

The reusable package is `packages/lazyingart-app-kit/` in Musia. Design and source
snapshots: `docs/lazyingart-app-framework.md`. Company remains the policy owner,
and EchoMind's active formal checkout remains the central service owner.

## For the Other App Sessions

Read the framework document and package README before adopting. It includes
versioned discovery/profile fixtures, a Node BFF protocol client, explicit
persistent flow/vault interfaces, refresh failure handling, and feature/readiness
validators. The tests inside the package can run independently in another repo.

```sh
npm test --prefix packages/lazyingart-app-kit
node tools/check_lazyingart_app.mjs --manifest apps/shared/lazyingart-app.json
```

Use `--require-ready` only as an additional release gate; the checker is offline
and does not verify live provider calls. Musia correctly fails that gate because
shared login is disabled and no production clients are registered.

## Ownership and Next Actions

| Owner | Requested action | Not authorized by this handoff |
| --- | --- | --- |
| EchoMind | Review compatibility with `fc05a2a6`; supply deployed issuer, exact registrations and callback evidence when ready | New issuer guessed by clients; invitation-gated general signup |
| Bunko | Review Node adapter for a successor candidate; preserve GitHub path, notes and drafts | Changes to build 8 in review; false attribution of posts |
| OnlyIdeas | Review adapter; retain legacy IDs and proof-backed links, private papers/jobs | Publishing private data because login succeeded |
| LazyArtCoin | Reuse fixtures in the owner's Python implementation; distinguish identity/access and nullable credits | New wallet owner IDs, balance merges, conversion or automatic spending |
| Musia | Register separate clients later; keep native learning guest-first and Studio isolated | Login UI, uploads or costly jobs exposed in the current guest release |

Required before activation: persistent encrypted app sessions, atomic one-use
attempts and refresh leases, server CSRF/ownership checks, native app links,
provider roundtrips, revocation, crash/offline/draft tests, dual-proof linking,
deletion/retention and updated privacy/reviewer evidence for each exact candidate.

Share a reviewed package version/contract, not a copied authentication database
or unrestricted EchoMind session. No other app worktree, native binary, store
submission, wallet or live session was modified by this framework task.

This note is a review request, not a claim that any peer has adopted the package.
