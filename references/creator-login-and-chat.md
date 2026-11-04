# Creator Login and Chat

## Account Boundary

Musia delegates sign-in to `https://chat.lazying.art/account`. It does not collect
or store an account password. The browser's saved-password selection belongs to
that login origin, not the Musia app session. A suggested legacy password is not
evidence that a password or an account was changed.

Use a saved entry belonging to the actual login site and intended account.
Do not copy temporary app credentials onto the shared login entry. Removal or
editing of saved passwords remains a user-controlled operation. Musia must not
read the password manager, merge accounts by email, or broaden associated-domain
entitlements to make autofill appear to work.

The central identity owner qualifies login form/autofill changes. Musia owns its
callback, local session, browser return page and native completion. Shared login
does not share subscriptions or generation allowances.

## Browser Return

The HTTPS callback terminates the issuer's form redirect with a no-store HTML
page. It attempts one app return and retains a user-tappable return link. Android
also receives an explicit-package intent for `art.lazying.musia`. No browser
fallback URL contains completion codes. Links expire with the native attempt.

Only the attempt ID and one-use completion code enter the custom-scheme URL.
Tokens, passwords and the PKCE verifier do not. The page removes the completed
callback query from browser history. Native exchange still requires the exact
locally held attempt, platform and verifier; replay and expiry fail closed.

Apple clients handle both ASWebAuthenticationSession completion and an app-root
URL callback for a still-active attempt. A deadline ends an abandoned browser
wait. Account UI closes only after Musia has exchanged and verified its session.
This change does not implement cold-start recovery of an expired/pending attempt.

Browser policy can require a user gesture before opening an external app:
[Chrome intent guidance](https://developer.chrome.com/docs/android/intents).
Apple native authentication uses the system session:
[AuthenticationServices](https://developer.apple.com/documentation/authenticationservices/authenticating-a-user-through-a-web-service).
Saved-password behavior must be assessed separately:
[Password AutoFill](https://developer.apple.com/documentation/security/password-autofill).

## Conversation

Chat is the default workspace. The composer stays at the bottom of the available
viewport; only the conversation scrolls. Song references and focus are optional.
The editable lyric/arrangement form lives in Song details. Sending a message
shows a working state and preserves the draft on failure. Manual edits made
during a response retain priority. Each account has its own draft/history.

A renderable brief exposes Generate song in the conversation. Generation still
requires explicit rights/visibility confirmation and a server-side allowance.
Private remains the default. Confirmed jobs show their actual queue, rendering,
review or playable state. Visible clients refresh job state every 15 seconds;
background views do not start new polling requests. Draft creation is not audio
generation, and a queued job is not a playable song.

The environment-configured API now observes the existing supervisor ownership
lock before advertising or admitting generation. A missing, idle or unsafe lock
means generation is unavailable; text chat and listening remain independent.
This is a queue-ownership check, not a GPU-health or audio-quality guarantee.
The bounded pilot still requires manual input and output approval. Renewing an
idle polling window carries only its remaining authorized render budget.

## Regression Checks

Run creator server tests in its pinned Python environment, and browser checks in
the standard `musia` environment against an isolated loopback preview:

```bash
python -m unittest discover -s tests -p 'test_creator*.py'
python -m unittest discover -s tests -p 'test_native_return_script.py'
conda run -n musia python tools/test_creator_ui.py --chromium /usr/bin/google-chrome
```

The browser fixture uses synthetic identity and agent responses, not real user
accounts. It covers 320/390/768/1440 widths, icon loading, fixed composer including
queued jobs, account-scoped persistence, draft sharing, concurrent edits, learning
without draft mutation, failed-message recovery, explicit render confirmation,
private defaults, and uninterrupted audio during social actions.

Native qualification additionally needs real system-browser return/cancel/expiry
on iPhone, Mac and Android, keyboard/safe-area checks, account switching and
foreground/background job progress. Source changes and local Android builds do
not constitute TestFlight delivery or a completed real-device login round trip.
