import AppKit
import MusiaCore
import SwiftUI

enum MacSection: String, CaseIterable, Identifiable {
    case library = "Library", practice = "Practice", lessons = "Lessons", create = "Create", community = "Community", settings = "Settings"
    var id: String { rawValue }
    var symbol: String {
        switch self {
        case .library: "music.note.list"
        case .practice: "guitars"
        case .lessons: "book"
        case .create: "sparkles"
        case .community: "person.2"
        case .settings: "gearshape"
        }
    }
}

@MainActor
final class MacNavigation: ObservableObject {
    @Published var section: MacSection? = .library
}

@main
@MainActor
struct MusiaMacApp: App {
    @StateObject private var catalog = CatalogStore()
    @StateObject private var creator = CreatorStore()
    @StateObject private var billing = CreatorBillingStore()
    @StateObject private var history: LocalStore
    @StateObject private var player: PlaybackController
    @StateObject private var navigation = MacNavigation()

    init() {
        let history = LocalStore()
        _history = StateObject(wrappedValue: history)
        _player = StateObject(wrappedValue: PlaybackController(history: history))
    }

    private var content: some View {
        MacRootView()
                .environmentObject(catalog)
                .environmentObject(history)
                .environmentObject(player)
                .environmentObject(navigation)
                .environmentObject(creator)
                .environmentObject(billing)
                .task { await creator.start(player: player) }
                .task(id: creator.identity) { billing.start(creator: creator); await billing.accountChanged() }
                .tint(Palette.teal)
                .preferredColorScheme(.light)
                .frame(minWidth: 1040, minHeight: 680)
                .background(MacWindowConfiguration())
                .onReceive(NotificationCenter.default.publisher(for: NSApplication.willTerminateNotification)) { _ in
                    player.checkpoint()
                }
#if DEBUG
                .task {
                    if ProcessInfo.processInfo.arguments.contains("--musia-review") {
                        await MacReview.run(catalog: catalog, history: history, player: player, navigation: navigation, creator: creator)
                    }
                }
#endif
    }

    var body: some Scene {
        WindowGroup("Musia") { content }
        .commands {
            CommandGroup(replacing: .newItem) {}
            SidebarCommands()
            CommandMenu("Playback") {
                Button(player.isPlaying ? "Pause" : "Play") { player.togglePlayback() }
                    .keyboardShortcut(.space, modifiers: [])
                    .disabled(!player.ready)
                Button("Back 10 Seconds") { player.seek(to: player.position - 10) }
                    .keyboardShortcut(.leftArrow, modifiers: .command).disabled(!player.ready)
                Button("Forward 10 Seconds") { player.seek(to: player.position + 10) }
                    .keyboardShortcut(.rightArrow, modifiers: .command).disabled(!player.ready)
                Divider()
                Button("Slower") { player.setRate(player.rate - 0.05) }.keyboardShortcut("[", modifiers: .command)
                Button("Faster") { player.setRate(player.rate + 0.05) }.keyboardShortcut("]", modifiers: .command)
                Button("Normal Speed") { player.setRate(1) }
                Divider()
                Button("Set Loop Start") { player.markA() }.disabled(!player.ready)
                Button("Set Loop End") { player.markB() }
                    .disabled(!player.ready || player.markerA.map { player.position - $0 < 0.1 } != false)
                Button("Clear Loop") { player.clearLoop() }.disabled(player.loop == nil && player.markerA == nil)
            }
            CommandMenu("Navigate") {
                ForEach(Array(MacSection.allCases.enumerated()), id: \.element) { index, section in
                    Button(section.rawValue) { navigation.section = section }
                        .keyboardShortcut(KeyEquivalent(Character(String(index + 1))), modifiers: .command)
                }
            }
            CommandGroup(replacing: .help) {
                Link("Musia Support", destination: URL(string: "https://musia.lazying.art/support")!)
                Link("Privacy Policy", destination: URL(string: "https://musia.lazying.art/privacy")!)
            }
        }
    }
}

private struct MacWindowConfiguration: NSViewRepresentable {
    func makeNSView(context: Context) -> WindowView { WindowView() }
    func updateNSView(_ view: WindowView, context: Context) {}

    final class WindowView: NSView {
        private var configured = false
        override func viewDidMoveToWindow() {
            super.viewDidMoveToWindow()
            guard !configured, let window else { return }
            configured = true
            window.identifier = NSUserInterfaceItemIdentifier("main")
            window.contentMinSize = NSSize(width: 1040, height: 680)
            if !window.setFrameUsingName("MusiaMainWindow") {
                window.setContentSize(NSSize(width: 1280, height: 800))
            }
            window.setFrameAutosaveName("MusiaMainWindow")
        }
    }
}

struct MacRootView: View {
    @EnvironmentObject private var navigation: MacNavigation
    @EnvironmentObject private var player: PlaybackController
    private var showPractice: Binding<Bool> {
        Binding(get: { navigation.section == .practice }, set: { if $0 { navigation.section = .practice } })
    }

    var body: some View {
        Group {
            if #available(macOS 13, *) {
                NavigationSplitView {
                    sidebar.navigationSplitViewColumnWidth(min: 170, ideal: 190, max: 240)
                } detail: { detail }
            } else {
                HSplitView {
                    sidebar.frame(minWidth: 170, idealWidth: 190, maxWidth: 240)
                    detail.frame(maxWidth: .infinity, maxHeight: .infinity)
                }
            }
        }.font(.system(size: 15))
    }

    private var sidebar: some View {
            List(MacSection.allCases, selection: $navigation.section) { section in
                Label(section.rawValue, systemImage: section.symbol)
                    .font(.body).padding(.vertical, 6).tag(section)
                    .accessibilityIdentifier("sidebar.\(section.rawValue.lowercased())")
            }
            .navigationTitle("Musia")
    }

    private var detail: some View {
            MusiaNavigation {
                Group {
                    switch navigation.section ?? .library {
                    case .library: LibraryView(showPractice: showPractice)
                    case .lessons: LessonsView(showPractice: showPractice)
                    case .settings: SettingsView()
                    case .create: CreatorView()
                    case .community: CreatorCommunityView()
                    case .practice:
                        if player.hasSelection { PracticeView() }
                        else {
                            VStack(spacing: 16) {
                                MusiaEmptyView("Ready to play", systemImage: "guitars",
                                               description: Text("Choose a song or begin with First Pulse."))
                                Button("Start First Pulse") { player.open(id: FirstPulse.id, localExercise: true) }
                                    .buttonStyle(.borderedProminent)
                            }
                        }
                    }
                }
            }
            .safeAreaInset(edge: .bottom, spacing: 0) {
                if player.hasSelection && navigation.section != .practice {
                    MiniPlayer(showPractice: showPractice)
                }
            }
    }
}
