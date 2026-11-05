# Musia 0.2.2 Internal Testing

Verified November 5, 2026. This is internal distribution, not a public release
or a replacement for an App Store review candidate.

| Platform | Build | Verified State |
| --- | --- | --- |
| iOS, with Watch companion | 12 | VALID, IN_BETA_TESTING; attached to the existing Musia Internal group |
| Android | 10 | Available on the existing internal-testing track |
| macOS | Unchanged | No new Mac binary delivered in this round |

The existing internal owner membership was verified. Email receipt was not
independently checked and no duplicate invitation was sent.

## Changes

- System-browser sign-in return handling validates the active, expiring native
  attempt and supports an explicit return action when automatic navigation fails.
- Shared-account sign-in is distinguished from legacy application testing access.
  Saved browser passwords are not read, reset or merged by Musia.
- Create opens with a conversational composer; song settings remain secondary.
  The composer stays above the keyboard and pending work can refresh its status.
- The original sound-bar icon and existing subscription, invitation and rights
  boundaries remain unchanged.

## Evidence

iOS source commit: `f40e8dbbff338f408a9ed5a59ae5476d1714196f`.

| Artifact | SHA-256 |
| --- | --- |
| iOS IPA | `97f5436980369f6d855601b1ebe5691aec5e421160e39397bb090eea9720bc77` |
| Android AAB | `9f1903d9e180cdead9accbc77c985136e81b321b67f1ac98da9b9ac2a9551b29` |

The iOS Darwin suite executed 71 tests with one existing opt-in skip and no
failures. Both selected native UI tests passed: keyboard-safe Create composition
and Stage/Practice switching with portrait/landscape transport checks. Four
genuine simulator captures were reviewed. Android release unit tests, lint,
packaging and the selected workspace/stage checks passed; its interrupted
practice run is not counted as a pass.

The signed iOS artifact was retained after an initial cleanup refusal. A separate
causally attributed export-log cleanup and independent preservation readback
passed before the first Linux upload. The original failure records were not
rewritten. Apple subsequently confirmed the complete upload, exact processed
build relationship, internal-group attachment and unchanged formal attachments.

## Test Limitations

- The shared KVM simulator has incomplete graphics and an audio-device limitation.
  Layout checks do not establish audible physical-device playback.
- The new native authenticated browser return and saved-password suggestions
  still need physical-device confirmation. No password-manager vault was edited.
- Physical Watch and iPad behavior were not requalified by these selected tests.
- A real full-song generation was not exercised in this test-build qualification.
  Existing invitation, usage, rights and approval checks remain in force; public
  paid checkout was not enabled.

Private upload journals, artifacts, captures and delivery receipts remain under
`store/.runtime/`. Reconcile those existing records before any retry; do not
upload another copy of these builds or invite the same tester again.
