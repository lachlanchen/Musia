# Musia Learning App Rules

- Native means SwiftUI/AVFoundation on iOS and Kotlin/Compose/Media3 on Android;
  do not replace them with a PWA shell or WebView.
- Keep the shared learning API contract compatible across web and native clients.
- Do not expose the existing Studio shell, sessions, filesystem or model workers
  through the learning site's public API.
- Use the audio player's source-time clock for beats, chords, lyrics and loops.
  Scale tap offsets into wall time when playback rate changes. Do not infer
  downbeats or time signature from the index of automatically detected beats.
- Automatically analyzed songs are estimates. Only known reference exercises or
  separately reviewed scores can be marked verified. Do not fake guitar grades.
- First Pulse instructions only apply to First Pulse, not arbitrary songs.
- Progress and creative drafts are local until a reviewed authentication/privacy
  design exists. Do not silently upload recordings or trigger paid generation.
- Prefer existing shared SDKs and signing toolchains. Each app owns its bundle ID,
  provisioning profile, upload-key configuration and store metadata.
- Secrets, private tester recipients, raw account/session logs and build products
  stay out of Git. Verify provider results before claiming invitations or review.
- Validate desktop/mobile layouts with screenshots and actual playback, and
  native background/interruption behavior on a device before claiming it works.
