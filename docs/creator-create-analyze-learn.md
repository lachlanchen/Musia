# Create, Analyze, Learn

Musia's Agent workspace has three conversation focuses. Studio remains the
editable song brief; generation is a separate, confirmed action.

| Focus | Behavior |
| --- | --- |
| Create | Discuss an idea, refine lyrics and arrangement, and update the shared draft. |
| Analyze | Explain the selected recording's saved lyric, chord, beat and melody evidence. |
| Learn | Suggest a small beginner practice step using the selected evidence, or explain general music theory. |

Select a library song or a reviewed creation and a start time in seconds. The
server supplies a bounded 20-second excerpt. The current selectors use the song's
default vocal; the request contract also supports an explicit `asset_id`.
Analyze and Learn cannot overwrite the draft, even if the model tries. A failed
turn restores its input without replacing newer typing. Account changes still
invalidate late replies and clear the selected private context.

## Evidence And Limits

`Chat.reference` accepts only a source, identifier, optional vocal identifier and
position. It accepts no URL, file path, client-generated evidence or tool command.
The server resolves catalog visibility and creator ownership before calling the
model. Unlisted songs are not restored by this feature. Older clients can omit
the new fields; clients send them only when `agentContextVersion >= 1`.

The assistant receives saved data, not the waveform. It cannot claim fresh ASR,
audio listening, measured pitch, a verified score or a performance grade. Catalog
analysis keeps its existing confidence labels. First Pulse is a known exercise;
its beat/chord evidence is verified. Reviewed creations currently provide their
corrected timed lyrics, but do not yet provide chord/beat/melody analysis through
the creator-song contract. These fields remain explicitly unavailable. Running
new audio analysis and attaching it to creations is separate follow-up work.

Chord explanations should cite source timestamps, not invented bar numbers or
downbeats. A slower practice tempo does not alter those timestamps. Empty capped
arrays mean data is absent from this excerpt, not necessarily the entire song.
LLM explanations still require judgment; successful contract tests are not proof
that every musical explanation is correct.

## Songwriting Direction

Treat personal events as inspiration rather than a checklist for the lyrics.
Use concrete imagery, emotional subtext, a recurring motif and natural phrasing.
Leave space for breath and sustained notes without imposing a mechanical word
limit. Reference songs may inform broad qualities, but their words and melody
must not be copied. Keep production instructions out of the sung text.

This changes drafting guidance, not the proven ACE full-song route or its audio
review requirements. A generated file is not automatically a finished song.
Input approval, listening, ASR/source comparison, omitted-line and tail audits,
timed lyric correction and publication review remain separate gates.

## Backend And Deployment

Direct DeepSeek is the live text backend. The optional AgInTi adapter is a bounded
JSON specialist, not a developer shell/session. Both have fixed endpoints,
response/body limits, whole-request deadlines and limited concurrency. Apple chat
requests now allow 105 seconds; Android chat allows a 110-second whole call.
Other request timeouts stay unchanged.

The immutable creator release includes reviewed catalog JSON so server-side song
references do not depend on a writable checkout or arbitrary network fetches.
`tools/creator_release.py --catalog-root <reviewed-checkout>` selects that snapshot.
Audio, covers, secrets and model weights are not added to that catalog snapshot.
Catalog updates require updating the creator snapshot as well as the learning API
when newly added songs should become available as chat references.

The pilot remains invitation-gated with public checkout disabled. A finite queue
can stop after its polling limit even when no render allowance was spent.
`tools/renew_creator_polling.py` renews only an exhausted window: it requires an
inactive daemon, exact prior configuration, no uncertain worker outcome and a
new run ID, and carries forward only the unused action/render allowance. It does
not grant account credits, approve inputs/outputs or auto-publish anything.
Run without `--apply` first. Renewal is an explicit operator action, not a timer
that replenishes budgets.

## Verification, 2026-10-24

- All 230 backend creator tests passed, including four renewal tests covering
  unused allowance, active-daemon refusal, uncertain outcomes and configuration
  tampering.
- Android debug Kotlin/Compose compilation and all 54 unit tests passed.
- Five real Swift conversation-model tests passed in the existing Linux Swift
  container. This is not an iOS/macOS SwiftUI build. The Linux image lacks the
  async URLSession methods used by Apple networking, so transport tests remain
  for the coordinated Apple build lane; no production workaround was added.
- Browser fixtures passed at 1440, 768, 390 and 320 pixels. Draft reload, history,
  concurrent Studio edits, read-only learning, failure recovery, private default,
  explicit render confirmation and uninterrupted social playback were checked.
  Desktop/mobile screenshots were inspected, including conversation height.
- Eight optional AgInTi adapter tests passed using the existing isolated image
  with the updated contract. No tools, credentials or persistent developer
  sessions were delegated to the model.
- Six synthetic direct DeepSeek calls were made across two prompt iterations.
  The final three completed in 9.03, 16.32 and 2.45 seconds. Manual review caught
  ambiguous bar-group wording in the first iteration; the revised prompt produced
  correct Em/Am timestamps and distinguished practice from source evidence.
  No audio was rendered, no customer account was accessed and no purchase occurred.

Reproduce backend tests with the dedicated creator-server Python environment and
the context subset with `PYTHONNOUSERSITE=1` in `musia`. Run
`tools/test_creator_ui.py` against an isolated loopback preview, not live identity.
`tools/check_creator_context_live.py --confirm-provider-calls --evidence <private-dir>`
uses the configured provider for exactly three synthetic text turns; its raw
responses belong outside Git. Rebuild the optional AgInTi contract with
`tools/export_creator_agent_contract.py` and verify it with `--check`.

Native changes are source-tested/prepared, not newly uploaded to TestFlight or
Google Play in this round. Apple UI/device QA and store delivery remain pending.
