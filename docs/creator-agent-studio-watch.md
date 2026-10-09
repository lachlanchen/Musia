# Agent, Studio and Watch

## Workspace Contract

The owner asked for conversational music creation by default, with a structured
workspace that the agent can update. The two tabs are **Agent** and **Studio**.
This is one song draft, not two independent forms. Opening or reloading Create
defaults to Agent; Studio exposes title, intent, lyrics, vocal language,
arrangement, duration, BPM and key.

- A chat request contains the latest draft and up to 12 user/assistant messages,
  at most 4,000 characters per message and 16,000 across history. Clients also
  enforce a 45,000-byte JSON body before the 48,000-byte ingress boundary.
- History stays inside the untrusted user envelope; it cannot introduce system
  or tool messages. The current Studio values take precedence over old history.
- Draft replies may ask a useful clarification without inventing completed
  lyrics. Rendering still requires the complete, validated brief.
- Every field manually changed during a request is retained, even if the user
  changed it back. The response updates only untouched fields. Responses from
  a previous account or session cannot alter the next account's workspace.
- Chat never submits a render. Rendering requires explicit rights confirmation
  and a separate confirmation action, with owner-bound idempotent recovery.
- Web storage and native Keychain/Keystore workspaces are scoped to the signed-in
  account. Logout clears the visible workspace; deletion removes that account's
  local workspace. This is **not cross-device chat synchronization**.
- The web prevents editing until initial identity loading finishes, so a fast
  keystroke cannot be overwritten by the account's restored draft. Icon rendering
  does not wait for job or account network requests.

Implementation: `musia/creator/{contracts,agent}.py`, `apps/web/creator/`,
Swift `CreatorModels`, `CreatorStore`, `CreatorView`, and Android's corresponding
`CreatorModels`, `CreatorRules`, `CreatorVault`, `CreatorViewModel`, `CreatorScreens`.

## Apple Watch Companion

The single native SwiftUI watchOS target requires watchOS 10 and a paired iPhone.
It is embedded in the iPhone app, not a separate store app or a WebView.

Playback shows the selected song, current source chord and its confidence,
source time, effective BPM and playback speed. Commands are explicit play/pause,
ten-second seek and speed from 25% to 200%. Missing analysis stays unavailable;
the Watch does not guess chords. A separate foreground practice page has a
40-200 BPM visual/haptic metronome and 2, 3, 4 or 6 beats per bar.

The companion transfers no session credentials, private audio URLs or lyrics.
Bounded, versioned snapshots expire after 30 seconds. Commands expire after
15 seconds, deduplicate by ID, and bind to the playback generation plus an asset
fingerprint so an old command cannot act on a newly selected vocal. Metronome
deadlines use `ContinuousClock`; missed beats are skipped, never burst-replayed.
The metronome stops when inactive. It does not request workout, microphone or
background-execution privileges just to keep haptics alive.

Sources: `WatchShared/WatchProtocol.swift`, `Musia/Services/WatchCompanionBridge.swift`,
`MusiaWatch/MusiaWatchApp.swift`, `WatchResources/`, and the iOS project generator.

Apple references:
[single-target setup](https://developer.apple.com/documentation/watchos-apps/setting-up-a-watchos-project),
[WatchConnectivity](https://developer.apple.com/documentation/WatchConnectivity/transferring-data-with-watch-connectivity),
[haptic playback](https://developer.apple.com/documentation/watchkit/wkinterfacedevice/play(_:)),
[App Store provisioning](https://developer.apple.com/help/account/provisioning-profiles/create-an-app-store-provisioning-profile).
Simulator UI is not proof of paired physical Watch connectivity or felt haptics.

## Repeatable Verification

`tests/test_creator_conversation.py` covers role/content/history limits and the
untrusted provider envelope. Swift `CreatorConversationTests` and Android
`CreatorContractTest` cover matching limits, shared-draft merging and payload
bounds. Six `MusiaCatalogTests` cover coalesced independent loads and cancellation:
discarding a sidebar view must not cancel the app's catalog fetch and leave an
empty library. Five `WatchProtocolTests` cover stale, malformed and wrong-selection
messages. Store tests cover the exact embedded Watch identity and scoped profile
creation, reusing the pinned distribution certificate without issuing a new one.

```bash
# Existing creator-server environment, not a cloned GPU environment.
~/.local/share/musia/creator-server/venv/bin/python -m unittest discover -s tests -p 'test_creator*.py'
~/.local/share/musia/creator-server/venv/bin/python -m unittest discover -s tools/store/tests

# Start the local preview separately, then test with the existing browser.
PYTHONNOUSERSITE=1 conda run -n musia python tools/test_creator_ui.py --chromium /usr/bin/google-chrome

# Mac, one build/test at a time; use the existing Xcode.
swift test --package-path apps/ios
```

`tools/check_creator_agent_live.py` performs exactly two real text-provider calls
using an already authenticated private QA fixture/browser. It verifies the
Studio title, conversation history, tempo edit, reload, and unchanged job list,
then restores browser workspace storage. It requires `--confirm-provider-calls`;
it never purchases or generates audio. An initial attempt raced account loading
and dispatched no provider request; the corrected run passed with two provider
requests.

Native tools: `android_creator_workspace_smoke.py` verifies the actual guest UI
and tab-shared draft; `android_stage_smoke.py` verifies timed chords, three lyric
languages, transport bounds and an advancing audio clock. `run_creator_ios_qa.py`
has separate `account`, `workspace`, `products` and `private-playback` cases.
It builds an isolated UI-test project from the signed candidate's exact source;
this is not execution of the signed distribution IPA. Private fixture credentials
and screenshots stay under Git-ignored `store/.runtime/`.

## Test Release Discipline

iOS/macOS 0.2.0 (9) are VALID / IN_BETA_TESTING in the existing owner group;
Android 0.2.0 (7) is available to internal testers. These are test updates,
not replacements for the held production releases. Exact delivery receipts
belong in the dated Apple/Android store records. The iPhone build includes Watch.

Use `tools/store/musia_store.py setup-apple-watch` to inspect the scoped profile
plan, then `--confirm-setup` for the authorized Watch ID/profile. It registers
only `art.lazying.musia.watchkitapp`, creates no new App Store app, and does not
revoke certificates. Set its exact protected path as `apple_watch_profile_path`.
`build_creator_apple.sh ios|macos` checks disk and peer build activity, reuses
existing signing material, and never uploads. It preserves current and previous
archives; obsolete Musia DerivedData may be removed without deleting evidence.

Do not replace the formal 0.1.2 (4) Apple reviews or publish the held Google
production release. Do not repeat already accepted uploads. Public paid checkout
remains disabled. Google Creator/Studio no-charge cycles passed on internal 6;
Apple transactions and remaining financial cases are not qualified. Password
sign-in is live; central Apple/Google/GitHub OAuth providers are still unavailable.
Generation remains an invitation-gated pilot with manual input/output approval.
