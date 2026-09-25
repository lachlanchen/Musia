import MusiaCore
import SwiftUI

struct LibraryView: View {
    @EnvironmentObject private var catalog: CatalogStore
    @EnvironmentObject private var player: PlaybackController
    @Binding var showPractice: Bool
    @State private var search = ""

    private var filtered: [MusiaCore.LibraryItem] {
        catalog.items.filter { matches($0) }
    }

    var body: some View {
        List {
            Section("On this device") {
                if matches(FirstPulse.item) {
                    Button {
                        player.open(id: FirstPulse.id, localExercise: true)
                        showPractice = true
                    } label: { LibraryRow(item: FirstPulse.item, local: true) }
                    .buttonStyle(.plain)
                    .accessibilityIdentifier("library.localFirstPulse")
                }
            }
            Section("Music library") {
                if catalog.loadingLibrary { ProgressView("Loading library...").padding(.vertical) }
                if let error = catalog.libraryError {
                    ErrorNotice(message: error) { Task { await catalog.loadLibrary(force: true) } }
                }
                ForEach(filtered) { item in
                    Button {
                        player.open(id: item.id)
                        showPractice = true
                    } label: { LibraryRow(item: item) }
                    .buttonStyle(.plain)
                }
                if !catalog.loadingLibrary && catalog.libraryError == nil && filtered.isEmpty {
                    ContentUnavailableView(search.isEmpty ? "No songs yet" : "No matching songs",
                                           systemImage: "music.note.list")
                }
            }
        }
        .listStyle(.plain)
        .navigationTitle("Musia")
        .searchable(text: $search, prompt: "Songs and artists")
        .refreshable { await catalog.loadLibrary(force: true) }
        .task { await catalog.loadLibrary() }
    }

    private func matches(_ item: MusiaCore.LibraryItem) -> Bool {
        search.isEmpty || "\(item.title) \(item.artist)".localizedCaseInsensitiveContains(search)
    }
}

private struct LibraryRow: View {
    let item: MusiaCore.LibraryItem
    var local = false

    var body: some View {
        HStack(alignment: .center, spacing: 14) {
            CoverView(url: item.coverUrl, local: local)
            VStack(alignment: .leading, spacing: 4) {
                Text(item.title).font(.headline).foregroundStyle(Palette.ink)
                Text(item.artist).font(.subheadline).foregroundStyle(.secondary)
                Text("\(item.kind) - \(Timeline.timestamp(item.duration))")
                    .font(.subheadline).foregroundStyle(local ? Palette.teal : .secondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            Image(systemName: "chevron.right").foregroundStyle(.secondary).accessibilityHidden(true)
        }
        .padding(.vertical, 6)
        .contentShape(Rectangle())
        .accessibilityElement(children: .combine)
    }
}
