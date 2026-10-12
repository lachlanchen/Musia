import AVFoundation
import MusiaCore
import SwiftUI

struct PitchMatchView: View {
    @ObservedObject var sound: PracticeSound
    @EnvironmentObject private var player: PlaybackController
    @StateObject private var capture = PitchCapture()
    @Environment(\.scenePhase) private var scenePhase
    @State private var note = 0
    @State private var lowerOctave = true

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Match a note").font(.title2.bold())
            Picker("Target note", selection: $note) {
                ForEach(0..<8, id: \.self) { Text(BeginnerPractice.syllables[$0]).tag($0) }
            }.disabled(capture.busy)
            Toggle("Lower octave", isOn: $lowerOctave).disabled(capture.busy)
            Text("Listen, let the tone stop, then hum or sing gently. Choose a comfortable octave; do not strain.")
            ViewThatFits(in: .horizontal) {
                HStack { controls }
                VStack(alignment: .leading, spacing: 12) { controls }
            }
            if let message = capture.message { Text(message).foregroundStyle(.secondary) }
            if let result = capture.result {
                Text("\(result.inTunePercent)% within half a semitone").font(.title2.bold()).foregroundStyle(Palette.coral)
                Text("\(result.voicedSeconds, specifier: "%.1f") seconds of clear pitch · \(Int(result.medianCents.rounded())) cents from target")
                Text(abs(result.medianCents) <= 50 ? "You found the note. Repeat gently, then try the next step."
                     : result.medianCents > 0 ? "Your note is higher. Listen again and glide down gently."
                     : "Your note is lower. Listen again and glide up gently.")
            }
            Text("On-device pitch estimate, not a singing-quality grade. One voice only; no backing music. A semitone is 100 cents. The three-second take is deleted after measurement and is never uploaded.")
                .font(.footnote).foregroundStyle(.secondary)
        }
        .onChange(of: note) { _, _ in capture.result = nil; capture.message = nil; sound.stop() }
        .onChange(of: lowerOctave) { _, _ in capture.result = nil; capture.message = nil; sound.stop() }
        .onChange(of: scenePhase) { _, phase in if phase != .active { capture.cancel() } }
        .onChange(of: sound.playing) { _, playing in if playing { capture.cancel() } }
        .onChange(of: player.isPlaying) { _, playing in if playing { capture.cancel() } }
        .onDisappear { capture.cancel() }
#if os(iOS)
        .onReceive(NotificationCenter.default.publisher(for: AVAudioSession.interruptionNotification)) { _ in capture.cancel() }
        .onReceive(NotificationCenter.default.publisher(for: AVAudioSession.routeChangeNotification)) { notification in
            if let value = notification.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt,
               value == AVAudioSession.RouteChangeReason.oldDeviceUnavailable.rawValue { capture.cancel() }
        }
#endif
    }
    @ViewBuilder private var controls: some View {
        Button {
            capture.cancel(); sound.play(BeginnerPractice.tone(note, lowerOctave: lowerOctave))
        } label: { Label("Listen", systemImage: "speaker.wave.2") }.buttonStyle(.bordered)
        Button {
            sound.stop()
            if capture.busy { capture.cancel() }
            else { capture.start(targetHz: BeginnerPractice.frequency(note) / (lowerOctave ? 2 : 1)) }
        } label: { Label(capture.busy ? "Stop" : "Sing · 3 seconds", systemImage: capture.busy ? "stop.fill" : "mic") }
            .buttonStyle(.borderedProminent)
    }
}
