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
        tabs
        .sheet(isPresented: $showPractice) {
            NavigationStack { PracticeView() }
                .presentationDragIndicator(.visible)
        }
    }

    private var tabs: some View {
        TabView {
            page { LibraryView(showPractice: $showPractice) }
                .tabItem { Label("Library", systemImage: "music.note.list") }
            page { LessonsView(showPractice: $showPractice) }
                .tabItem { Label("Lessons", systemImage: "book") }
            page { SettingsView() }
                .tabItem { Label("Settings", systemImage: "gearshape") }
        }
    }

    private func page<Content: View>(@ViewBuilder content: () -> Content) -> some View {
        NavigationStack {
            // Reserve space inside each tab, never outside TabView's navigation safe area.
            content().safeAreaInset(edge: .bottom, spacing: 0) {
                if player.hasSelection {
                    MiniPlayer(showPractice: $showPractice)
                }
            }
            .toolbarBackground(.visible, for: .tabBar)
            .toolbarBackground(Color(.systemBackground), for: .tabBar)
        }
    }
}
