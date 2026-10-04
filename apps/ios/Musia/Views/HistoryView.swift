import MusiaCore
import SwiftUI
import UniformTypeIdentifiers

private struct HistoryDocument: FileDocument {
    static var readableContentTypes: [UTType] { [.json] }
    var data: Data
    init(data: Data) { self.data = data }
    init(configuration: ReadConfiguration) throws { data = configuration.file.regularFileContents ?? Data() }
    func fileWrapper(configuration: WriteConfiguration) throws -> FileWrapper {
        FileWrapper(regularFileWithContents: data)
    }
}

struct HistoryView: View {
    @EnvironmentObject private var history: LocalStore
    @EnvironmentObject private var player: PlaybackController
    @State private var confirmReset = false
    @State private var exporting = false
    @State private var document = HistoryDocument(data: Data())
    @State private var exportError: String?

    var body: some View {
        List {
            Section {
                LabeledContent("Sessions", value: String(history.records.count))
                LabeledContent("Practice time", value: Timeline.timestamp(history.records.reduce(0) { $0 + $1.seconds }))
            } footer: {
                Text("Stored on this device. No account or server progress. Up to 200 recent sessions.")
            }
            if let error = history.error { Text(error).foregroundStyle(Palette.coral) }
            if history.records.isEmpty {
                ContentUnavailableView("No practice yet", systemImage: "clock.arrow.circlepath")
            }
            ForEach(history.records) { record in
                VStack(alignment: .leading, spacing: 6) {
                    Text(record.title).font(.headline)
                    Text(record.date, format: .dateTime.month().day().hour().minute())
                        .font(.subheadline).foregroundStyle(.secondary)
                    Text("\(record.mode.rawValue) - \(Timeline.timestamp(record.seconds)) - \(record.rate, specifier: "%.2g")x")
                    if let mean = record.meanAbsoluteOffset {
                        Text("\(record.tapCount) taps - mean absolute offset \(Int(mean.rounded())) ms")
                            .font(.subheadline).foregroundStyle(Palette.teal)
                    }
                }
                .padding(.vertical, 6)
            }
            Section {
                Button(role: .destructive) { confirmReset = true } label: {
                    Label("Reset local data", systemImage: "trash")
                }
            } footer: {
                Text("Tap offsets compare screen taps with reference beats, not singing or instrument performance. Device and Bluetooth latency can affect them.")
            }
        }
        .listStyle(.plain)
        .navigationTitle("History")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    player.checkpoint()
                    do { document = HistoryDocument(data: try history.export()); exporting = true }
                    catch { exportError = error.localizedDescription }
                } label: { Image(systemName: "square.and.arrow.up") }
                .accessibilityLabel("Export history as JSON").help("Export history as JSON")
            }
        }
        .onAppear { player.checkpoint() }
        .confirmationDialog("Reset history and practice preferences?", isPresented: $confirmReset, titleVisibility: .visible) {
            Button("Reset local data", role: .destructive) { player.resetLocalData() }
            Button("Cancel", role: .cancel) { }
        } message: { Text("Playback will pause. This cannot be undone.") }
        .fileExporter(isPresented: $exporting, document: document, contentType: .json,
                      defaultFilename: "musia-history") { result in
            if case .failure(let error) = result { exportError = error.localizedDescription }
        }
        .alert("Export failed", isPresented: Binding(get: { exportError != nil }, set: { if !$0 { exportError = nil } })) {
            Button("OK") { exportError = nil }
        } message: { Text(exportError ?? "") }
    }
}
