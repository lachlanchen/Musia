# Deferred Creator Qualification

Owner checkpoint: October 9, 2026. The owner explicitly asked to retain these
unfinished items for later and switch current work to the Fun player and song
writing. This list is not an automatic schedule or permission to enable sales.

- [ ] Shared Apple, Google and GitHub sign-in: coordinate the central identity
  provider, use Musia's registered client, test callbacks/account linking,
  cancellation, revocation and logout before showing provider buttons.
- [ ] Apple purchase qualification: complete product metadata, then verify
  no-charge sandbox purchase, renewal, restore, expiry/refund and owner-bound
  entitlements. Never substitute a real-charge purchase.
- [ ] Physical Apple Watch: paired iPhone playback, chord/BPM freshness,
  disconnect/reconnect, stale-command rejection, foreground metronome and
  felt haptics. Simulator success is not physical-device evidence.
- [ ] Public launch decision after qualification: paid checkout remains off;
  generation remains invitation-gated with manual input/output approval.
  Do not remove these gates merely because the UI or test build is delivered.

Keep existing formal reviews unchanged. Current test releases: Android
0.2.0 (7), iPhone and Mac 0.2.0 (9), with Watch included in the iPhone build.
See [acceptance matrix](creator-billing-acceptance.md),
[Agent/Studio/Watch](creator-agent-studio-watch.md), and the private OneTimeSync
Musia handoff for evidence and device coordination. Recheck live capabilities
and store state before resuming; these are checkpoint values, not eternal facts.
