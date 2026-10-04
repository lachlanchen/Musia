import MusiaCore
import SwiftUI

enum Palette {
    static let teal = Color(red: 0.00, green: 0.43, blue: 0.43)
    static let coral = Color(red: 0.77, green: 0.23, blue: 0.20)
    static let mint = Color(red: 0.90, green: 0.98, blue: 0.96)
    static let ink = Color(red: 0.09, green: 0.15, blue: 0.16)
    static var surface: Color {
#if os(macOS)
        Color(nsColor: .controlBackgroundColor)
#else
        Color(.secondarySystemBackground)
#endif
    }
}

struct CoverView: View {
    let url: URL?
    var local = false
    var size: CGFloat = 64

    var body: some View {
        Group {
            if local {
                Image("FirstPulseCover").resizable().scaledToFill()
            } else if let url, APIClient.isSecureRemoteURL(url) {
                AsyncImage(url: url) { phase in
                    switch phase {
                    case .success(let image): image.resizable().scaledToFill()
                    case .failure: placeholder(symbol: "photo")
                    default: placeholder(symbol: "music.note")
                    }
                }
            } else { placeholder(symbol: "music.note") }
        }
        .frame(width: size, height: size)
        .clipped()
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .accessibilityHidden(true)
    }

    private func placeholder(symbol: String) -> some View {
        ZStack {
            Palette.mint
            Image(systemName: symbol).font(.title2).foregroundStyle(Palette.teal)
        }
    }
}

struct ErrorNotice: View {
    let message: String
    let retry: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Unable to load", systemImage: "exclamationmark.triangle")
                .font(.headline).foregroundStyle(Palette.coral)
            Text(message).font(.body).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true)
            Button(action: retry) { Label("Retry", systemImage: "arrow.clockwise") }
                .buttonStyle(.bordered)
        }
        .padding(.vertical, 8)
    }
}

struct ConfidenceLabel: View {
    let name: String
    let value: AnalysisConfidence

    var body: some View {
        Label("\(name): \(value.label)", systemImage: value == .verified ? "checkmark.seal" : "info.circle")
            .font(.subheadline)
            .foregroundStyle(value == .verified ? Palette.teal : .secondary)
            .fixedSize(horizontal: false, vertical: true)
    }
}

struct TransportButton: View {
    let title: String
    let symbol: String
    var primary = false
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: symbol)
                .font(primary ? .largeTitle : .title2)
                .frame(width: primary ? 64 : 48, height: primary ? 64 : 48)
                .background(primary ? Palette.teal : Palette.mint, in: Circle())
                .foregroundStyle(primary ? .white : Palette.teal)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(title)
        .help(title)
    }
}

struct MiniPlayer: View {
    @EnvironmentObject private var player: PlaybackController
    @Binding var showPractice: Bool

    var body: some View {
        HStack(spacing: 12) {
            Button { showPractice = true } label: {
                HStack(spacing: 12) {
                    CoverView(url: player.song?.coverUrl, local: player.isLocalExercise, size: 44)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(player.song?.title ?? (player.loading ? "Loading..." : "Practice"))
                            .font(.headline).lineLimit(1)
                        Text(player.issue != nil ? "Playback unavailable" : player.mode.rawValue)
                            .font(.subheadline).foregroundStyle(.secondary).lineLimit(1)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("mini.open")
            TransportButton(title: player.isPlaying || player.waiting ? "Pause" : "Play",
                            symbol: player.isPlaying || player.waiting ? "pause.fill" : "play.fill") {
                player.togglePlayback()
            }
            .disabled(!player.ready)
            .accessibilityIdentifier("mini.play")
        }
        .padding(.horizontal, 16).padding(.vertical, 8)
        // Keep compact transport readable without displacing tabs in landscape.
        // Opening the full player retains the user's unrestricted Dynamic Type size.
        .dynamicTypeSize(...DynamicTypeSize.xxxLarge)
        .background(Palette.surface)
        .overlay(alignment: .top) { Divider() }
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("mini.player")
    }
}
