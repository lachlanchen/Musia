# Apple Resubmission: 0.1.2 (4)

## Confirmed Outcome

Fresh App Store Connect API readback on October 6, 2026 at 06:20 Hong Kong time:

| Platform | Version | Build | Version / submission state | Resubmitted (Hong Kong) |
| --- | --- | --- | --- | --- |
| iPhone / iPad | 0.1.2 | 4 | WAITING_FOR_REVIEW | 06:19:56 |
| macOS | 0.1.2 | 4 | WAITING_FOR_REVIEW | 06:12:47 |

iOS build: `7b0ae745-7e3b-44ab-9100-1de68e99cfc7`.
Mac build: `1d5a2c57-de54-4120-a219-5a4b158265f5`.
The exact signed packages already delivered to TestFlight were reused. No binary
was rebuilt or uploaded again. Manual release, USD2.99 pricing and existing
territories remain unchanged. Google Play was not modified in this task.
Submission is not approval, resolution of Apple's concern, or public release.

## Rejection And Response

Both 0.1.1 submissions were rejected under guidelines 4.3 and 4.2.6. Apple's
message raised originality/spam/template concerns and requested nine detailed
answers; it did not identify a crash or a specific broken control. It cautioned
against simply resubmitting an unchanged app or changing metadata/build numbers.

Sent a separate response in each platform's existing review conversation, with:

- All nine answers: actual problem/audience, workflow, beta feedback, other
  company-app scopes, consolidation, shared code, third-party tools and ownership.
- A five-page PDF with the full answers, test limitations, a 0.1.2 walkthrough
  and two genuine unedited native screenshot examples.
- Explicit distinction between the previously submitted 0.1.1 and the substantive
  beginner-practice/multilingual features in 0.1.2; no claim that a new number
  alone establishes compliance or that the native app contains AI generation.
- Disclosure of internal GlassAgent repository references and reused company
  development infrastructure; no blanket claim that all development is isolated.

The response appeared with its PDF attachment in each thread (Messages: 2).
Then selected the already-tested 0.1.2 (4) builds, updated version descriptions
and reviewer walkthroughs, used Update Review, and resubmitted each once.
Apple accepted both review requests. Its substantive originality decision remains
pending; do not blindly repeat this submission if the response is insufficient.

Source text: [full answers](apple-review-answers-2026-10-06.md) and
[short reply](apple-review-reply-2026-10-06.txt).
The exact submitted PDF remains private under
`store/.runtime/rejection-20261006/Musia-App-Review-Answers.pdf`.

## Changes Presented In 0.1.2

These were implemented before the rejection, not invented in the review reply:

- Independent EN/ZH/JA lyric selections, readings and per-vocal translation sets.
- Local Do Re Mi references and first-answer listening quiz scores.
- Audio-clocked 40-160 BPM metronome and optional Em/Am changes.
- Practice history moved below Settings.

No microphone recording, singing grade or automated instrument evaluation is
claimed. Existing navigation-safe mini-player and chord-shape fixes were already
in 0.1.1; the response does not falsely present them as new fixes to this rejection.

Added two current native screenshots to each iPhone/iPad store gallery: Do Re Mi
and Metronome. iPhone images are 1320x2868; iPad images are 2064x2752. All 12
images across both galleries read back COMPLETE with no delivery errors. The
existing native player/guitar screenshots were retained; no screenshots were
fabricated, stretched, or substituted with website captures.

## Verification And Limits

- Existing exact-artifact evidence: see [internal delivery](testflight-0.1.2.md)
  and [native release verification](native-update-2026-10-05.md).
- 42 release-tool tests passed again locally.
- Inspected native source imports/targets: Apple frameworks and Musia modules,
  no third-party runtime package or embedded web shell in these targets.
- Exact-file comparison of 22 Musia Swift files with tracked Swift in ten other
  company workspaces found no whole-file matches. This does not prove absence
  of shared fragments, common ideas or development tooling.
- A fresh iPhone simulator run on the physical Mac mini passed
  `testBeginnerPracticeAndSettings` in 27.523 seconds. The SSH tunnel dropped
  during the next test. The remaining run is not marked passed. Earlier network
  and KVM audio-device limitations remain disclosed in the reviewer evidence.
- No active local build or upload remains. The mini's remote test/process state
  could not be rechecked because its pinned route became unavailable. Private
  handoff records the exact owned simulator/result bundle for cleanup when that
  host returns. Do not terminate a peer's runtime or report cleanup as verified.

Provider evidence and operation journals are under
`store/.runtime/rejection-20261006/` and `store/.runtime/formal/actions/`.
The shared browser/profile was preserved; only the task-owned tab is disposable.

## Next Review

1. Read both exact version and review-submission states before doing anything.
2. Preserve these pending submissions; do not duplicate requests or upload build4.
3. If Apple asks for more specificity, answer the named concern with actual
   product/code/content evidence. If it identifies insufficient differentiation,
   implement real changes and test them before a new submission.
4. Distinguish owner feedback, automated tests, device tests and unverified claims.
   Never inflate beta participation or promise approval.

References: [Apple's review guidelines](https://developer.apple.com/app-store/review/guidelines/),
[replying to App Review](https://developer.apple.com/help/app-store-connect/manage-submissions-to-app-review/reply-to-app-review-messages/).
