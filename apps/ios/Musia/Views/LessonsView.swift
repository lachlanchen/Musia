import MusiaCore
import SwiftUI

struct LessonsView: View {
    @EnvironmentObject private var player: PlaybackController
    @Binding var showPractice: Bool

    var body: some View {
        List {
            Section("Start here") {
                NavigationLink { BeginnerPracticeView(rhythm: false) } label: {
                    Label("Do Re Mi · Listen and learn", systemImage: "ear")
                }
                .accessibilityIdentifier("lesson.pitch")
                NavigationLink { BeginnerPracticeView(rhythm: true) } label: {
                    Label("First Pulse · Rhythm workshop", systemImage: "metronome")
                }
                .accessibilityIdentifier("lesson.metronome")
                NavigationLink { BeginnerPracticeView(rhythm: true, progression: 1) } label: {
                    Label("Chord changes · Play along", systemImage: "guitars")
                }
            }
            Section("Pulse practice") {
                Button {
                    player.open(id: FirstPulse.id, localExercise: true)
                    showPractice = true
                } label: {
                    Label {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("First Pulse").font(.headline)
                            Text("60 BPM - Verified beats - Synthesized audio")
                                .font(.subheadline).foregroundStyle(.secondary)
                        }
                    } icon: { Image(systemName: "metronome").foregroundStyle(Palette.coral) }
                }
                .buttonStyle(.plain)
            }
        }
        .listStyle(.plain)
        .navigationTitle("Lessons")
    }
}
