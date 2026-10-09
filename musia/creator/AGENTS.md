# Creator Boundary

- Keep public listening and social features outside the generation paywall.
- Confirmed 2026-10-09 targets: Free 2 renders/month; Creator US$9.99/20;
  Studio US$29.99/80. Private generation is allowed on every tier.
- A central login, an invitation, an operator pilot grant and a verified paid
  subscription are different authorities. Never interchange them.
- Do not expose Studio, filesystem paths, client-controlled commands/model names,
  arbitrary URLs or credentials through this API. Use fixed private worker jobs.
- Preserve atomic reserve/settle/release, owner-bound idempotency, per-user limits
  and the single GPU claim. Unknown worker outcomes require reconciliation.
- Never auto-publish planned lyrics. The selected audio owns the corrected text
  and timing; require listening, large ASR, source comparison and gap/tail audit.
- No public signup/payment deployment until the release gates in
  `docs/musia-creator-agent.md` are qualified. Do not describe the local pilot as
  real OAuth, a verified purchase or an end-to-end production render.
- Test in the musia conda env and the separate Python 3.11+ creator-server env
  when touching auth. Do not upgrade the GPU env just to install the account SDK.
- Store credentials/media/receipts outside Git. Coordination notes default to
  `/home/lachlan/Nutstore Files/OneTimeSync/Musia/`.
