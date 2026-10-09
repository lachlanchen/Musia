#if os(iOS)
import Combine
import CryptoKit
import Foundation
import MusiaCore
import WatchConnectivity

@MainActor
final class WatchCompanionBridge: NSObject, ObservableObject, WCSessionDelegate {
    private weak var player: PlaybackController?
    private var updates: AnyCancellable?
    private var commandGuard = WatchCommandGuard()
    private var lastPublished: WatchPlaybackSnapshot?

    func start(player: PlaybackController) {
        guard self.player == nil, WCSession.isSupported() else { return }
        self.player = player
        let session = WCSession.default
        session.delegate = self
        session.activate()
        updates = Timer.publish(every: 1, on: .main, in: .common).autoconnect()
            .sink { [weak self] _ in self?.publish() }
    }

    private func snapshot() -> WatchPlaybackSnapshot {
        guard let player, player.hasSelection, let song = player.song else { return WatchPlaybackSnapshot() }
        let asset = player.asset
        let hasChords = asset?.confidence.chords != .unavailable
        let chord = hasChords ? Timeline.current(in: asset?.chords ?? [], at: player.position)?.name : nil
        let hasBeats = asset?.confidence.beats != .unavailable && !(asset?.beats.isEmpty ?? true)
        let assetHash = SHA256.hash(data: Data((asset?.id ?? "").utf8)).prefix(8).map { String(format: "%02x", $0) }.joined()
        return WatchPlaybackSnapshot(selection: player.selectionGeneration.uuidString + ":" + assetHash,
            title: String(song.title.prefix(240)), chord: chord,
            chordConfidence: asset?.confidence.chords.label ?? "Unavailable",
            bpm: hasBeats ? asset?.bpm : nil,
            position: min(player.duration, max(0, player.position)), duration: max(0, player.duration),
            rate: player.rate, playing: player.isPlaying, ready: player.ready)
    }

    private func publish(force: Bool = false) {
        let session = WCSession.default
        guard session.activationState == .activated, session.isPaired, session.isWatchAppInstalled else { return }
        let state = snapshot()
        // Keep a heartbeat for freshness, but do not queue high-frequency background traffic.
        if !force, let old = lastPublished, !session.isReachable,
           old.selection == state.selection, old.playing == state.playing, old.ready == state.ready { return }
        guard let data = state.encoded() else { return }
        do {
            try session.updateApplicationContext(["playback": data])
            lastPublished = state
        } catch { return }
        if session.isReachable { session.sendMessageData(data, replyHandler: nil, errorHandler: { _ in }) }
    }

    nonisolated func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        Task { @MainActor [weak self] in self?.publish(force: true) }
    }
    nonisolated func sessionReachabilityDidChange(_ session: WCSession) {
        Task { @MainActor [weak self] in self?.publish(force: true) }
    }
    nonisolated func sessionDidBecomeInactive(_ session: WCSession) {}
    nonisolated func sessionDidDeactivate(_ session: WCSession) { session.activate() }

    nonisolated func session(_ session: WCSession, didReceiveMessageData messageData: Data,
                             replyHandler: @escaping (Data) -> Void) {
        guard messageData.count <= 2048,
              let command = try? JSONDecoder().decode(WatchPlaybackCommand.self, from: messageData) else {
            replyHandler(Data()); return
        }
        Task { @MainActor [weak self] in
            guard let self else { replyHandler(Data()); return }
            let current = self.snapshot()
            if self.commandGuard.accept(command, selection: current.selection, ready: current.ready), let player = self.player {
                switch command.action {
                case .refresh: break
                case .play: player.play()
                case .pause: player.pause()
                case .seek: if let value = command.value { player.seek(to: value) }
                case .rate: if let value = command.value { player.setRate(value) }
                }
            }
            replyHandler(self.snapshot().encoded() ?? Data())
            self.publish(force: true)
        }
    }
}
#endif
