# Login and Chat Internal Test

Version 0.2.2 keeps the existing icon, library, playback and account boundaries.
The Create screen opens directly into chat, with song details available separately.
Its composer stays above the keyboard; job progress refreshes while the screen is
visible. Browser sign-in includes an explicit return action and expires safely.

## Test Checklist

1. Open Create while signed out. Check the composer at normal and large text
   sizes, with the keyboard open and closed.
2. Start LazyingArt sign-in. Confirm the intended account before continuing.
   Complete it and check that Musia returns to the conversation. Cancel once,
   then start a fresh attempt; an expired or replayed link must not sign in.
3. Type a draft, open Song details, edit a title, then return to chat. Confirm
   draft content survives without sending or generating automatically.
4. Send a music idea with an invited account. Check the actual reply and progress;
   an API failure must show an error, never a fabricated finished song.
5. Play a song, switch pages and reopen the player. Confirm lyrics, chord diagrams
   and navigation remain usable. Check background playback on a physical device.

Generation remains an invitation-gated pilot with explicit render/rights controls
and operator approval. Paid checkout is not enabled by this update. Internal
build delivery does not replace a formal review candidate.

## Release Verification

Treat each platform independently: a successful compile is not a signed export;
an accepted upload is not a processed build or tester availability. Bind QA to
the exact source/artifact hash and preserve unresolved outcomes before retrying.

For Google Play, inspect the exact internal track and publishing overview before
mutation. Keep noninternal tracks unchanged and preserve `ERROR_IF_IN_REVIEW`.
Musia's internal submission rejects `changesNotSentForReview`; omit that flag.
If a commit fails after a successful upload, reconcile the existing edit instead
of uploading the AAB again. `tools/store/play_commit_recovery.py` supports a
bounded recovery with fresh artifact/QA/track checks. A committed edit may return
HTTP400 with the exact already-committed reason rather than404. Only that exact
reason is treated as closed; unrelated400 responses remain failures.

For Apple, acquire a new finite shared-Mac placement before native work. The
metadata entry verifies its complete source/helper pins, host and expiry, bounds
its own child processes and fails closed on incomplete cleanup. It is not build
admission. Native QA, signing, upload, processing and existing-group availability
must each have separate evidence. Preserve existing signing material, peer jobs,
review candidates and tester membership.

Saved passwords are browser-managed. Musia uses the shared issuer account, not a
separate app password. Stable field IDs/autocomplete hints can clarify forms but
cannot guarantee which saved account the browser suggests; do not reset or merge
accounts to address autofill confusion.

Provider references: [Play edit commit](https://developers.google.com/android-publisher/api-ref/rest/v3/edits/commit),
[Apple build uploads](https://developer.apple.com/documentation/appstoreconnectapi/build-uploads).
