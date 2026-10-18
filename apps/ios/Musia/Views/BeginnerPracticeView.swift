import AVFoundation
import MusiaCore
import SwiftUI

@MainActor
final class PracticeSound: NSObject, ObservableObject, AVAudioPlayerDelegate {
    private var audio: AVAudioPlayer?
    @Published var playing = false
    @Published var preparing = false
    private var preparation: Task<Void, Never>?
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
    func play(plan: PracticePlan) {
        stop(); preparing = true
        preparation = Task {
            let data = await Task.detached(priority: .userInitiated) { plan.audio() }.value
            guard !Task.isCancelled else { return }
            preparation = nil; preparing = false
            play(data, loop: true)
        }
    }
    func stop() { preparation?.cancel(); preparation = nil; preparing = false; audio?.stop(); audio = nil; playing = false }
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
    @State private var pitchMode = 0
    private var quiz: Bool { pitchMode == 1 }
    @State private var explored: Int?
    @State private var round = PitchRound(targets: [0, 1, 2, 0, 1, 2].shuffled())
    @State private var heard = false
    @State private var bpm = 60.0
    @State private var beats = 4
    @State private var subdivision = 1
    @State private var progression: Int
    @State private var pattern = PracticePattern.hold
    @State private var feedback = RhythmFeedback()
    @State private var tapTempo = TapTempo()
    let rhythm: Bool

    init(rhythm: Bool, progression: Int = 0) {
        self.rhythm = rhythm
        _progression = State(initialValue: progression)
    }
    private var plan: PracticePlan {
        PracticePlan(bpm: Int(bpm), beats: beats, subdivision: subdivision, progression: progression, pattern: pattern)
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                Text(rhythm ? "First Pulse" : "Hear Do, Re, Mi").font(.largeTitle.bold())
                if let issue = sound.issue { Text(issue).foregroundStyle(Palette.coral) }
                if rhythm { metronome } else { pitch }
            }
            .frame(maxWidth: 680, alignment: .leading).padding(24).frame(maxWidth: .infinity)
        }
        .navigationTitle(rhythm ? "Rhythm workshop" : "Do Re Mi")
        .onAppear { player.pause() }
        .onDisappear { sound.stop() }
        .onChange(of: player.isPlaying) { playing in if playing { sound.stop() } }
        .onChange(of: scenePhase) { phase in if phase != .active { sound.stop() } }
#if os(iOS)
        .onReceive(NotificationCenter.default.publisher(for: AVAudioSession.interruptionNotification)) { _ in sound.stop() }
        .onReceive(NotificationCenter.default.publisher(for: AVAudioSession.routeChangeNotification)) { note in
            if note.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt == AVAudioSession.RouteChangeReason.oldDeviceUnavailable.rawValue { sound.stop() }
        }
#endif
    }

    private var pitch: some View {
        VStack(alignment: .leading, spacing: 20) {
            Picker("Activity", selection: $pitchMode) {
                Text("Listen").tag(0)
                Text("Recognize").tag(1)
                Text("Sing").tag(2)
            }.pickerStyle(.segmented).onChange(of: pitchMode) { _ in reset() }
            if pitchMode == 2 {
                PitchMatchView(sound: sound)
            } else {
            Text("In this exercise Do is C. Re and Mi are the next two steps up.")
            Picker("Notes", selection: $count) {
                Text("Do Re Mi").tag(3)
                Text("Full octave").tag(8)
            }.pickerStyle(.segmented)
                .onChange(of: count) { _ in reset() }
            if quiz {
                MusiaFits {
                    HStack { quizReference; Spacer(); quizScore }
                } compact: {
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
    }

    private var quizReference: some View {
        Button { player.pause(); sound.play(BeginnerPractice.tone(0)) } label: { Label("Hear Do", systemImage: "speaker.wave.2") }
    }

    private var quizScore: some View {
        Text("\(round.correct) / \(round.answered) correct").font(.headline).monospacedDigit()
    }

    private var metronome: some View {
        VStack(alignment: .leading, spacing: 20) {
            Stepper(value: $bpm, in: 30...240, step: 1) {
                Text("\(Int(bpm)) BPM").font(.largeTitle.bold()).monospacedDigit()
            }.onChange(of: bpm) { _ in resetRhythm() }
            Slider(value: $bpm, in: 30...240, step: 1).accessibilityLabel("Tempo in beats per minute")
            Button {
                resetRhythm()
                if let tempo = tapTempo.tap(at: ProcessInfo.processInfo.systemUptime) { bpm = Double(tempo) }
            } label: { Label("Tap tempo", systemImage: "hand.tap") }.buttonStyle(.bordered)
            MusiaFits {
                HStack { rhythmButtons }
            } compact: {
                VStack(alignment: .leading, spacing: 12) { rhythmButtons }
            }
            Picker("Beats per bar", selection: $beats) {
                ForEach([2, 3, 4, 6], id: \.self) { Text("\($0)/4").tag($0) }
            }.pickerStyle(.segmented).onChange(of: beats) { _ in resetRhythm() }
            Picker("Clicks per beat", selection: $subdivision) {
                Text("Beat").tag(1); Text("Eighths").tag(2); Text("Triplets").tag(3)
            }.pickerStyle(.segmented).onChange(of: subdivision) { _ in resetRhythm() }
            Picker("Progression", selection: $progression) {
                ForEach(0..<PracticePlan.progressions.count, id: \.self) { Text(PracticePlan.progressions[$0]).tag($0) }
            }.onChange(of: progression) { _ in resetRhythm() }
            if progression > 0 {
                Picker("Pattern", selection: $pattern) {
                    ForEach(PracticePattern.allCases, id: \.self) { Text($0.rawValue).tag($0) }
                }.pickerStyle(.segmented).onChange(of: pattern) { _ in resetRhythm() }
            }
            TimelineView(.periodic(from: .now, by: 0.05)) { _ in
                let beat = sound.playing ? plan.beat(at: sound.time) : -1
                LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: beats > 4 ? 3 : beats), spacing: 12) {
                    ForEach(0..<beats, id: \.self) { index in
                        Text("\(index + 1)").font(.title.bold()).frame(maxWidth: .infinity, minHeight: 60)
                            .foregroundStyle(beat == index ? Color.white : Palette.ink)
                            .background(beat == index ? Palette.coral : Palette.mint, in: RoundedRectangle(cornerRadius: 8))
                    }
                }
                if let chord = plan.chord(at: sound.time), let shape = GuitarShape.known(chord) {
                    Text(chord).font(.largeTitle.bold()).foregroundStyle(Palette.coral)
                    GuitarDiagram(shape: shape)
                }
            }
            if progression > 0 {
                Text(pattern == .hold ? "Strum once on 1. Let it ring, prepare the next shape, then change on the next 1."
                     : pattern == .strum ? "One relaxed down-strum per beat. Keep the pulse moving while you change shape."
                     : "Listen to the chord tones one at a time. Pick slowly and evenly; the reference is synthesized, not a recording of guitar strings.")
            }
            if !feedback.offsets.isEmpty {
                Text("\(feedback.offsets.count) taps · average offset \(Int(feedback.averageOffset.rounded())) ms")
                    .font(.headline).monospacedDigit()
                if let score = feedback.inTimePercent(bpm: Int(bpm)) {
                    Text("\(score)% within the timing window").font(.title2.bold()).foregroundStyle(Palette.coral)
                    Text(abs(feedback.bias) < 25 ? "Your taps are centered on the beat. Keep the motion relaxed."
                         : feedback.bias > 0 ? "Mostly after the click. Prepare your next tap a little sooner."
                         : "Mostly before the click. Listen for the click and ease back slightly.")
                }
            }
            Text("BPM is beats per minute; 60 BPM is one beat per second. Tap feedback uses a window of 8% of a beat, at least 40 ms. Bluetooth and touch latency can affect the result. This is tap timing, not a guitar performance grade.")
                .font(.footnote).foregroundStyle(.secondary)
        }
    }

    @ViewBuilder private var rhythmButtons: some View {
                Button {
                    if sound.playing || sound.preparing { sound.stop() }
                    else { player.pause(); feedback = RhythmFeedback(); sound.play(plan: plan) }
                } label: { Label(sound.preparing ? "Preparing" : sound.playing ? "Stop" : "Start", systemImage: sound.playing || sound.preparing ? "stop.fill" : "play.fill") }
                    .buttonStyle(.borderedProminent)
                    .accessibilityIdentifier("metronome.startStop")
                Button {
                    feedback.tap(playback: sound.time, monotonic: ProcessInfo.processInfo.systemUptime, bpm: Int(bpm))
                } label: { Label("Tap the beat", systemImage: "hand.tap") }
                    .buttonStyle(.bordered).disabled(!sound.playing)
                    .accessibilityIdentifier("metronome.tap")
    }

    private func resetRhythm() { sound.stop(); feedback = RhythmFeedback() }

    private func reset() {
        round = PitchRound(targets: (count == 3 ? [0, 1, 2, 0, 1, 2] : Array(0..<8)).shuffled())
        heard = false; explored = nil; sound.stop()
    }
}
