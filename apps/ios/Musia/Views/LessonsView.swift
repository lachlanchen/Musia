import MusiaCore
import SwiftUI

struct LessonsView: View {
    @EnvironmentObject private var catalog: CatalogStore
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
                    Label("Metronome & chord changes", systemImage: "metronome")
                }
                .accessibilityIdentifier("lesson.metronome")
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
            Section("Lessons") {
                if catalog.loadingLessons { ProgressView("Loading lessons...") }
                if let error = catalog.lessonsError {
                    ErrorNotice(message: error) { Task { await catalog.loadLessons(force: true) } }
                }
                ForEach(catalog.lessons) { lesson in
                    NavigationLink {
                        LessonDetail(lesson: lesson, showPractice: $showPractice)
                    } label: {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(lesson.title).font(.headline)
                            Text(lesson.focus).font(.subheadline).foregroundStyle(.secondary)
                        }
                        .padding(.vertical, 6)
                    }
                }
                if catalog.lessons.isEmpty && !catalog.loadingLessons && catalog.lessonsError == nil {
                    ContentUnavailableView("No lessons yet", systemImage: "book")
                }
            }
        }
        .listStyle(.plain)
        .navigationTitle("Lessons")
        .task { await catalog.loadLessons() }
        .refreshable { await catalog.loadLessons(force: true) }
    }
}

private struct LessonDetail: View {
    let lesson: Lesson
    @Binding var showPractice: Bool
    @EnvironmentObject private var player: PlaybackController

    var body: some View {
        List {
            Section {
                Text(lesson.title).font(.title2.bold())
                Text(lesson.focus).foregroundStyle(Palette.teal)
                Text(lesson.body)
            }
            Section("Practice") {
                ForEach(Array(lesson.steps.enumerated()), id: \.offset) { index, step in
                    HStack(alignment: .top, spacing: 12) {
                        Text("\(index + 1)").font(.headline).foregroundStyle(Palette.coral)
                        Text(step).fixedSize(horizontal: false, vertical: true)
                    }
                    .padding(.vertical, 4)
                }
                Button {
                    player.open(id: lesson.exerciseId, localExercise: lesson.exerciseId == FirstPulse.id)
                    showPractice = true
                } label: { Label("Open exercise", systemImage: "play.circle") }
            }
        }
        .listStyle(.plain)
        .navigationTitle("Lesson")
#if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
#endif
    }
}
