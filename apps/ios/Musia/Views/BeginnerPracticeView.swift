import AVFoundation
import MusiaCore
import SwiftUI

@MainActor
final class PracticeSound: NSObject, ObservableObject, AVAudioPlayerDelegate {
    private var audio: AVAudioPlayer?
    @Published var playing = false
    @Published var issue: String?
    var time: Double { audio?.currentTime ?? 0 }

    @discardableResult func play(_ data: Data, loop: Bool = false) -> Bool {
        stop()
        do {
#if os(iOS)
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default)
            try AVAudioSession.sharedInstance().setActive(true)
#endif
            audio = try AVAudioPlayer(data: data)
            audio?.delegate = self
            audio?.numberOfLoops = loop ? -1 : 0
            audio?.prepareToPlay()
            guard audio?.play() == true else { throw CocoaError(.fileReadUnknown) }
            playing = true; issue = nil
            return true
        } catch { issue = "Could not play the practice sound. Try again."; return false }
    }
    func stop() { audio?.stop(); audio = nil; playing = false }
    nonisolated func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        Task { @MainActor [weak self, weak player] in
            guard let self, self.audio === player else { return }
            self.playing = false
        }
    }
}

struct BeginnerPracticeView: View {
    @EnvironmentObject private var player: PlaybackController
    @Environment(\.scenePhase) private var scenePhase
    @StateObject private var sound = PracticeSound()
    @State private var count = 3
    @State private var quiz = false
    @State private var explored: Int?
    @State private var round = PitchRound(targets: [0, 1, 2, 0, 1, 2].shuffled())
    @State private var heard = false
    @State private var bpm = 60.0
    @State private var chords = false
    @State private var tapping = [Double]()
    @State private var lastTapTime = -1.0
    let rhythm: Bool

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                Text(rhythm ? "Find your pulse" : "Hear Do, Re, Mi").font(.largeTitle.bold())
                if let issue = sound.issue { Text(issue).foregroundStyle(Palette.coral) }
                if rhythm { metronome } else { pitch }
            }
            .frame(maxWidth: 680, alignment: .leading).padding(24).frame(maxWidth: .infinity)
        }
        .navigationTitle(rhythm ? "Metronome" : "Do Re Mi")
        .onAppear { player.pause() }
        .onDisappear { sound.stop() }
        .onChange(of: player.isPlaying) { _, playing in if playing { sound.stop() } }
        .onChange(of: scenePhase) { _, phase in if phase != .active { sound.stop() } }
#if os(iOS)
        .onReceive(NotificationCenter.default.publisher(for: AVAudioSession.interruptionNotification)) { _ in sound.stop() }
        .onReceive(NotificationCenter.default.publisher(for: AVAudioSession.routeChangeNotification)) { note in
            if note.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt == AVAudioSession.RouteChangeReason.oldDeviceUnavailable.rawValue { sound.stop() }
        }
#endif
    }

    private var pitch: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Start by listening, not singing. In this exercise Do is C. Re and Mi are the next two steps up.")
            Picker("Activity", selection: $quiz) {
                Text("Learn").tag(false)
                Text("Quiz").tag(true)
            }.pickerStyle(.segmented).onChange(of: quiz) { _, _ in reset() }
            Picker("Notes", selection: $count) {
                Text("Do Re Mi").tag(3)
                Text("Full octave").tag(8)
            }.pickerStyle(.segmented)
                .onChange(of: count) { _, _ in reset() }
            if quiz {
                ViewThatFits(in: .horizontal) {
                    HStack { quizReference; Spacer(); quizScore }
                    VStack(alignment: .leading, spacing: 12) { quizReference; quizScore }
                }
            }
            if quiz {
            Text("Question \(round.index + 1) of \(round.targets.count)").font(.subheadline).foregroundStyle(.secondary)
            Button {
                player.pause(); heard = sound.play(BeginnerPractice.tone(round.target))
            } label: {
                Label("Listen to the note", systemImage: "play.fill").frame(maxWidth: .infinity, minHeight: 44)
            }.buttonStyle(.borderedProminent).accessibilityIdentifier("pitch.listen")
            }
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 88))], spacing: 12) {
                ForEach(0..<count, id: \.self) { note in
                    Button {
                        if quiz { round.choose(note) }
                        else { player.pause(); sound.play(BeginnerPractice.tone(note)); explored = note }
                    } label: {
                        VStack {
                            Text(BeginnerPractice.syllables[note]).font(.title2.bold())
                            Text("\(note % 7 + 1) · \(BeginnerPractice.noteNames[note])").font(.caption)
                        }.frame(maxWidth: .infinity, minHeight: 64)
                    }.buttonStyle(.bordered).disabled(quiz && (!heard || round.answer != nil))
                        .accessibilityIdentifier("pitch.note.\(note)")
                }
            }
            if !quiz, let explored {
                Text("\(BeginnerPractice.syllables[explored]) · \(BeginnerPractice.noteNames[explored]) · \(BeginnerPractice.frequency(explored), specifier: "%.1f") Hz")
                    .font(.headline).foregroundStyle(Palette.teal)
            }
            if quiz, let answer = round.answer {
                Label(answer == round.target ? "Correct" : "That was \(BeginnerPractice.syllables[round.target])",
                      systemImage: answer == round.target ? "checkmark.circle" : "ear")
                    .font(.title3).foregroundStyle(Palette.teal)
                Text("\(BeginnerPractice.syllables[round.target]) is \(BeginnerPractice.noteNames[round.target]). Replay and compare it with Do.")
                Button(round.finished ? "Practice again" : "Next note") {
                    if round.finished { reset() } else { round.next(); heard = false; sound.stop() }
                }.buttonStyle(.borderedProminent)
            }
            Text("Score counts your first answer to each listening question. It is not a singing or guitar grade.")
                .font(.footnote).foregroundStyle(.secondary)
        }
    }

    private var quizReference: some View {
        Button { player.pause(); sound.play(BeginnerPractice.tone(0)) } label: { Label("Hear Do", systemImage: "speaker.wave.2") }
    }

    private var quizScore: some View {
        Text("\(round.correct) / \(round.answered) correct").font(.headline).monospacedDigit()
    }

    private var metronome: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("BPM means beats per minute. At 60 BPM, each click is one second apart. Count 1, 2, 3, 4; the stronger click is 1.")
            LabeledContent("Tempo", value: "\(Int(bpm)) BPM").font(.title2.bold())
            Slider(value: $bpm, in: 40...160, step: 5, onEditingChanged: { editing in
                if editing { sound.stop(); tapping = [] } else { lastTapTime = -1 }
            }).accessibilityLabel("Tempo in beats per minute")
            Toggle("Em / Am chord practice", isOn: $chords).onChange(of: chords) { _, _ in sound.stop(); tapping = [] }
            TimelineView(.periodic(from: .now, by: 0.05)) { _ in
                let beat = sound.playing ? Int(sound.time / (60 / bpm)) : -1
                HStack(spacing: 12) {
                    ForEach(0..<4) { index in
                        Text("\(index + 1)").font(.title.bold()).frame(maxWidth: .infinity, minHeight: 64)
                            .foregroundStyle(beat % 4 == index ? Color.white : Palette.ink)
                            .background(beat % 4 == index ? Palette.teal : Palette.mint, in: RoundedRectangle(cornerRadius: 8))
                    }
                }
                if chords {
                    Text(beat < 0 || beat < 4 ? "Em" : "Am").font(.largeTitle.bold()).foregroundStyle(Palette.teal)
                    if let shape = GuitarShape.known(beat < 0 || beat < 4 ? "Em" : "Am") {
                        GuitarDiagram(shape: shape)
                    }
                }
            }
            if chords { Text("Start with one gentle down-strum on beat 1. Hold for four clicks, then change chord. You do not need to sing.") }
            ViewThatFits(in: .horizontal) {
                HStack { rhythmButtons }
                VStack(alignment: .leading, spacing: 12) { rhythmButtons }
            }
            if !tapping.isEmpty {
                Text("\(tapping.count) taps · average offset \(Int((tapping.reduce(0, +) / Double(tapping.count)).rounded())) ms")
                    .font(.headline).monospacedDigit()
            }
            Text("Tap timing is measured against the playback clock. Speaker and Bluetooth delay can affect it. Chords here are synthesized reference sounds, not an analysis of your playing.")
                .font(.footnote).foregroundStyle(.secondary)
        }
    }

    @ViewBuilder private var rhythmButtons: some View {
                Button {
                    if sound.playing { sound.stop() }
                    else { player.pause(); tapping = []; lastTapTime = -1; sound.play(BeginnerPractice.metronome(bpm: Int(bpm), chords: chords), loop: true) }
                } label: { Label(sound.playing ? "Stop" : "Start", systemImage: sound.playing ? "stop.fill" : "play.fill") }
                    .buttonStyle(.borderedProminent)
                    .accessibilityIdentifier("metronome.startStop")
                Button {
                    let time = sound.time
                    guard abs(time - lastTapTime) > 0.12 else { return }
                    lastTapTime = time
                    let beat = 60 / bpm
                    tapping.append(abs(time - (time / beat).rounded() * beat) * 1000)
                    tapping = Array(tapping.suffix(32))
                } label: { Label("Tap the beat", systemImage: "hand.tap") }
                    .buttonStyle(.bordered).disabled(!sound.playing)
                    .accessibilityIdentifier("metronome.tap")
    }

    private func reset() {
        round = PitchRound(targets: (count == 3 ? [0, 1, 2, 0, 1, 2] : Array(0..<8)).shuffled())
        heard = false; explored = nil; sound.stop()
    }
}
