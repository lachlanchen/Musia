import SwiftUI

@main
@MainActor
struct MusiaApp: App {
    @StateObject private var catalog = CatalogStore()
    @StateObject private var history: LocalStore
    @StateObject private var player: PlaybackController
    @Environment(\.scenePhase) private var scenePhase

    init() {
        let history = LocalStore()
        _history = StateObject(wrappedValue: history)
        _player = StateObject(wrappedValue: PlaybackController(history: history))
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(catalog)
                .environmentObject(history)
                .environmentObject(player)
                .tint(Palette.teal)
                .preferredColorScheme(.light)
                .onChange(of: scenePhase) { _, phase in
                    if phase != .active { player.checkpoint() }
                }
        }
    }
}

struct RootView: View {
    @EnvironmentObject private var player: PlaybackController
    @State private var showPractice = false

    var body: some View {
        TabView {
            NavigationStack { LibraryView(showPractice: $showPractice) }
                .tabItem { Label("Library", systemImage: "music.note.list") }
            NavigationStack { LessonsView(showPractice: $showPractice) }
                .tabItem { Label("Lessons", systemImage: "book") }
            NavigationStack { HistoryView() }
                .tabItem { Label("History", systemImage: "clock.arrow.circlepath") }
        }
        .safeAreaInset(edge: .bottom, spacing: 0) {
            if player.hasSelection { MiniPlayer(showPractice: $showPractice) }
        }
        .sheet(isPresented: $showPractice) {
            NavigationStack { PracticeView() }
                .presentationDragIndicator(.visible)
        }
    }
}
