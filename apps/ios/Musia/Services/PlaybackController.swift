import AVFoundation
import Combine
import MediaPlayer
import MusiaCore
import UIKit

@MainActor
final class PlaybackController: ObservableObject {
    @Published private(set) var song: Song?
    @Published private(set) var asset: SongAsset?
    @Published private(set) var isLocalExercise = false
    @Published private(set) var loading = false
    @Published private(set) var issue: String?
    @Published private(set) var position = 0.0
    @Published private(set) var duration = 0.0
    @Published private(set) var isPlaying = false
    @Published private(set) var waiting = false
    @Published private(set) var ready = false
    @Published private(set) var seeking = false
    @Published private(set) var rate: Double
    @Published private(set) var mode: PracticeMode
    @Published private(set) var loop: LoopRange?
    @Published private(set) var markerA: Double?
    @Published private(set) var tapFeedback: TapFeedback?
    @Published private(set) var tapMessage = "No taps yet"

    let history: LocalStore
    private let player = AVPlayer()
    private let api = APIClient()
    private var requestedID: String?
    private var loadTask: Task<Void, Never>?
    private var artworkTask: Task<Void, Never>?
    private var generation = UUID()
    private var seekGeneration = UUID()
    private var wantsPlayback = false
    private var resumeAfterInterruption = false
    private var statusObservation: NSKeyValueObservation?
    private var controlObservation: NSKeyValueObservation?
    private var durationObservation: NSKeyValueObservation?
    private var periodicObserver: Any?
    private var boundaryObserver: Any?
    private var notifications: [NSObjectProtocol] = []
    private var itemNotifications: [NSObjectProtocol] = []
    private var remoteTargets: [(MPRemoteCommand, Any)] = []
    private var artwork: MPMediaItemArtwork?
    private var record: PracticeRecord?
    private var activeSince: Date?
    private var lastCheckpoint = Date()
    private var lastNowPlayingSecond = -1
    private var lastTapBeat: Double?

    init(history: LocalStore) {
        self.history = history
        let storedRate = (UserDefaults.standard.object(forKey: "musia.rate.v1") as? Double) ?? 1
        rate = Timeline.clampedRate(storedRate)
        mode = PracticeMode(rawValue: UserDefaults.standard.string(forKey: "musia.mode.v1") ?? "") ?? .listen
        player.automaticallyWaitsToMinimizeStalling = true
        controlObservation = player.observe(\.timeControlStatus, options: [.new]) { [weak self] _, _ in
            Task { @MainActor [weak self] in self?.updatePlaybackState() }
        }
        periodicObserver = player.addPeriodicTimeObserver(
            forInterval: CMTime(seconds: 1.0 / 30, preferredTimescale: 600), queue: .main
        ) { [weak self] _ in
            Task { @MainActor [weak self] in self?.tick() }
        }
        observeSession()
        configureRemoteCommands()
    }

    var hasSelection: Bool { requestedID != nil }
    var beatConfidence: AnalysisConfidence { asset?.confidence.beats ?? .unavailable }
    var canTap: Bool {
        mode == .tap && isPlaying && !seeking && beatConfidence != .unavailable &&
            TapEvaluator.isWithinReference(time: position, beats: asset?.beats ?? [], loop: loop)
    }

    func open(id: String, localExercise: Bool = false) {
        if requestedID == id, isLocalExercise == localExercise, song != nil, issue == nil { return }
        finishRecord()
        loadTask?.cancel(); artworkTask?.cancel()
        pause()
        clearItem()
        generation = UUID()
        let token = generation
        requestedID = id; isLocalExercise = localExercise
        song = nil; asset = nil; artwork = nil
        position = 0; duration = 0; loop = nil; markerA = nil
        issue = nil; loading = true; resetTap()
        updateNowPlaying()
        loadTask = Task { [weak self] in
            guard let self else { return }
            do {
                let loaded: Song
                if localExercise {
                    let directory = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
                        .appendingPathComponent("Musia", isDirectory: true)
                    try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
                    let url = directory.appendingPathComponent("first-pulse-em-am-v1.wav")
                    if !FileManager.default.fileExists(atPath: url.path) {
                        // Small deterministic PCM render runs off the UI actor.
                        let data = await Task.detached(priority: .userInitiated) { FirstPulse.wavData() }.value
                        try Task.checkCancellation()
                        try data.write(to: url, options: .atomic)
                    }
                    loaded = try FirstPulse.song(audioURL: url)
                } else {
                    loaded = try await api.song(id: id)
                }
                try Task.checkCancellation()
                guard token == generation else { return }
                song = loaded
                loading = false
                if let initial = loaded.defaultAsset { selectAsset(initial.id) }
                loadArtwork(loaded.coverUrl)
            } catch {
                guard token == generation, !Task.isCancelled else { return }
                loading = false; issue = error.localizedDescription
            }
        }
    }

    func retry() {
        guard let id = requestedID else { return }
        open(id: id, localExercise: isLocalExercise)
    }

    func selectAsset(_ id: String) {
        guard let next = song?.assets.first(where: { $0.id == id }) else { return }
        finishRecord(); pause(); clearItem()
        asset = next; duration = next.duration; position = 0
        loop = nil; markerA = nil; issue = nil; resetTap()
        let item = AVPlayerItem(url: next.audioUrl)
        item.audioTimePitchAlgorithm = .spectral
        player.replaceCurrentItem(with: item)
        statusObservation = item.observe(\.status, options: [.initial, .new]) { [weak self] item, _ in
            Task { @MainActor [weak self] in
                guard let self, item === self.player.currentItem else { return }
                switch item.status {
                case .readyToPlay:
                    self.ready = true
                    self.readDuration()
                    self.issue = nil
                case .failed:
                    self.fail(self.playbackError(item.error))
                default: self.ready = false
                }
            }
        }
        durationObservation = item.observe(\.duration, options: [.new]) { [weak self] _, _ in
            Task { @MainActor [weak self] in self?.readDuration() }
        }
        itemNotifications.append(NotificationCenter.default.addObserver(
            forName: .AVPlayerItemDidPlayToEndTime, object: item, queue: .main
        ) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, item === self.player.currentItem else { return }
                if let loop = self.loop, self.wantsPlayback { self.seek(to: loop.start) }
                else { self.pause(); self.position = self.duration; self.checkpoint() }
            }
        })
        itemNotifications.append(NotificationCenter.default.addObserver(
            forName: .AVPlayerItemFailedToPlayToEndTime, object: item, queue: .main
        ) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, item === self.player.currentItem else { return }
                self.fail(item.error?.localizedDescription ?? "The audio stream stopped. Check your connection and retry.")
            }
        })
        updateNowPlaying()
    }

    func togglePlayback() { wantsPlayback ? pause() : play() }

    func play() {
        guard ready, issue == nil, asset != nil else { return }
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playback, mode: .default, policy: .longFormAudio)
            try session.setActive(true)
            wantsPlayback = true
            if position >= duration - 0.02 || loop.map({ position < $0.start || position >= $0.end }) == true {
                seek(to: loop?.start ?? 0)
            } else if !seeking { player.playImmediately(atRate: Float(rate)) }
            updateNowPlaying()
        } catch { fail("Audio session unavailable: \(error.localizedDescription)") }
    }

    func pause() {
        wantsPlayback = false
        resumeAfterInterruption = false
        player.pause()
        checkpoint()
        activeSince = nil
        isPlaying = false; waiting = false
        resetTap()
        updateNowPlaying()
    }

    func setRate(_ value: Double) {
        finishRecord()
        rate = Timeline.clampedRate(value)
        UserDefaults.standard.set(rate, forKey: "musia.rate.v1")
        resetTap()
        if wantsPlayback && !seeking { player.playImmediately(atRate: Float(rate)) }
        if isPlaying { beginRecord() }
        updateNowPlaying()
    }

    func setMode(_ value: PracticeMode) {
        finishRecord()
        mode = value
        UserDefaults.standard.set(value.rawValue, forKey: "musia.mode.v1")
        resetTap()
        if isPlaying { beginRecord() }
    }

    func seek(to time: Double) {
        guard ready else { return }
        checkpoint(); activeSince = nil
        let target = Timeline.clampedSeek(time, duration: duration, loop: loop)
        seekGeneration = UUID()
        let token = seekGeneration
        seeking = true; position = target; lastTapBeat = nil
        player.seek(to: CMTime(seconds: target, preferredTimescale: 600), toleranceBefore: .zero, toleranceAfter: .zero) {
            [weak self] finished in
            Task { @MainActor [weak self] in
                guard let self, token == self.seekGeneration else { return }
                self.seeking = false
                if finished && self.wantsPlayback {
                    self.player.playImmediately(atRate: Float(self.rate))
                    self.updatePlaybackState()
                }
                self.updateNowPlaying()
            }
        }
    }

    func setLoop(start: Double, end: Double) {
        guard let range = LoopRange(start: start, end: end, duration: duration) else {
            tapMessage = "B must be at least 0.1 seconds after A."
            return
        }
        loop = range; markerA = nil
        installLoopBoundary()
        seek(to: range.start)
    }

    func markA() { markerA = position }
    func markB() {
        guard let start = markerA else { return }
        setLoop(start: start, end: position)
    }

    func clearLoop() {
        loop = nil; markerA = nil
        removeLoopBoundary()
    }

    func tap() {
        guard canTap, player.timeControlStatus == .playing, let asset, !asset.beats.isEmpty else { return }
        let time = player.currentTime().seconds
        guard TapEvaluator.isWithinReference(time: time, beats: asset.beats, loop: loop) else { return }
        guard let feedback = TapEvaluator.evaluate(time: time, rate: rate, beats: asset.beats, loop: loop) else {
            tapFeedback = nil; tapMessage = "No nearby reference beat"; return
        }
        guard lastTapBeat != feedback.beatTime else { tapMessage = "Beat already tapped"; return }
        lastTapBeat = feedback.beatTime
        tapFeedback = feedback; tapMessage = feedback.label
        beginRecord()
        record?.tapCount += 1
        record?.absoluteOffsetTotal += abs(feedback.offsetMilliseconds)
    }

    func checkpoint() {
        if let since = activeSince {
            record?.seconds += max(0, Date().timeIntervalSince(since))
            activeSince = Date()
        }
        if let record, record.seconds >= 0.25 || record.tapCount > 0 { history.save(record) }
        lastCheckpoint = Date()
    }

    func resetLocalData() {
        pause()
        record = nil; activeSince = nil
        history.reset()
        UserDefaults.standard.removeObject(forKey: "musia.rate.v1")
        UserDefaults.standard.removeObject(forKey: "musia.mode.v1")
        rate = 1; mode = .listen; clearLoop(); resetTap()
        updateNowPlaying()
    }

    private func beginRecord() {
        guard let song, let asset else { return }
        if record == nil {
            record = PracticeRecord(songID: song.id, title: song.title, assetID: asset.id, mode: mode, rate: rate)
        }
        if activeSince == nil && isPlaying && !seeking { activeSince = Date() }
    }

    private func finishRecord() {
        checkpoint(); record = nil; activeSince = nil
    }

    private func resetTap() {
        lastTapBeat = nil; tapFeedback = nil; tapMessage = "No taps yet"
    }

    private func readDuration() {
        guard let value = player.currentItem?.duration.seconds, value.isFinite, value > 0 else { return }
        duration = value
        if let loop, loop.end > value { clearLoop() }
        updateNowPlaying()
    }

    private func updatePlaybackState() {
        let playing = player.timeControlStatus == .playing && !seeking
        if isPlaying && !playing { checkpoint(); activeSince = nil }
        isPlaying = playing
        waiting = player.timeControlStatus == .waitingToPlayAtSpecifiedRate
        if playing { beginRecord() }
        updateNowPlaying()
    }

    private func tick() {
        guard !seeking else { return }
        let value = player.currentTime().seconds
        guard value.isFinite else { return }
        position = max(0, value)
        if !TapEvaluator.isWithinReference(time: position, beats: asset?.beats ?? [], loop: loop) {
            tapFeedback = nil
        }
        if let loop, wantsPlayback, position >= loop.end { seek(to: loop.start); return }
        if Date().timeIntervalSince(lastCheckpoint) >= 5 { checkpoint() }
        if Int(position) != lastNowPlayingSecond {
            lastNowPlayingSecond = Int(position)
            updateNowPlaying()
        }
    }

    private func installLoopBoundary() {
        removeLoopBoundary()
        guard let loop else { return }
        boundaryObserver = player.addBoundaryTimeObserver(
            forTimes: [NSValue(time: CMTime(seconds: loop.end, preferredTimescale: 600))], queue: .main
        ) { [weak self] in
            Task { @MainActor [weak self] in
                guard let self, self.wantsPlayback, !self.seeking, let range = self.loop else { return }
                self.seek(to: range.start)
            }
        }
    }

    private func removeLoopBoundary() {
        if let boundaryObserver { player.removeTimeObserver(boundaryObserver) }
        boundaryObserver = nil
    }

    private func clearItem() {
        ready = false; seeking = false; seekGeneration = UUID()
        statusObservation = nil; durationObservation = nil
        removeLoopBoundary()
        itemNotifications.forEach(NotificationCenter.default.removeObserver)
        itemNotifications = []
        player.replaceCurrentItem(with: nil)
    }

    private func fail(_ message: String) {
        pause(); ready = false; issue = message
    }

    private func playbackError(_ error: Error?) -> String {
        guard let error = error as NSError? else { return "Audio could not be loaded." }
        var detail = "\(error.domain) \(error.code)"
        if let cause = error.userInfo[NSUnderlyingErrorKey] as? NSError {
            detail += "; \(cause.domain) \(cause.code)"
        }
        return "\(error.localizedDescription) (\(detail))"
    }

    private func observeSession() {
        notifications.append(NotificationCenter.default.addObserver(
            forName: AVAudioSession.interruptionNotification, object: nil, queue: .main
        ) { [weak self] notification in
            let type = notification.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt
            let options = (notification.userInfo?[AVAudioSessionInterruptionOptionKey] as? UInt) ?? 0
            Task { @MainActor [weak self] in
                guard let self else { return }
                if type == AVAudioSession.InterruptionType.began.rawValue {
                    let resume = self.wantsPlayback
                    self.pause(); self.resumeAfterInterruption = resume
                } else if type == AVAudioSession.InterruptionType.ended.rawValue {
                    let resume = self.resumeAfterInterruption &&
                        AVAudioSession.InterruptionOptions(rawValue: options).contains(.shouldResume)
                    self.resumeAfterInterruption = false
                    if resume { self.play() }
                }
            }
        })
        notifications.append(NotificationCenter.default.addObserver(
            forName: AVAudioSession.routeChangeNotification, object: nil, queue: .main
        ) { [weak self] notification in
            let reason = notification.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt
            if reason == AVAudioSession.RouteChangeReason.oldDeviceUnavailable.rawValue {
                Task { @MainActor [weak self] in self?.pause() }
            }
        })
        notifications.append(NotificationCenter.default.addObserver(
            forName: AVAudioSession.mediaServicesWereResetNotification, object: nil, queue: .main
        ) { [weak self] _ in
            Task { @MainActor [weak self] in self?.fail("The audio service restarted. Retry playback.") }
        })
    }

    private func configureRemoteCommands() {
        let center = MPRemoteCommandCenter.shared()
        addRemote(center.playCommand) { $0.play() }
        addRemote(center.pauseCommand) { $0.pause() }
        addRemote(center.togglePlayPauseCommand) { $0.togglePlayback() }
        center.skipBackwardCommand.preferredIntervals = [10]
        center.skipForwardCommand.preferredIntervals = [10]
        addRemote(center.skipBackwardCommand) { $0.seek(to: $0.position - 10) }
        addRemote(center.skipForwardCommand) { $0.seek(to: $0.position + 10) }
        center.changePlaybackPositionCommand.isEnabled = true
        let target = center.changePlaybackPositionCommand.addTarget { [weak self] event in
            guard let event = event as? MPChangePlaybackPositionCommandEvent else { return .commandFailed }
            let time = event.positionTime
            Task { @MainActor [weak self] in self?.seek(to: time) }
            return .success
        }
        remoteTargets.append((center.changePlaybackPositionCommand, target))
        center.nextTrackCommand.isEnabled = false
        center.previousTrackCommand.isEnabled = false
    }

    private func addRemote(_ command: MPRemoteCommand, action: @escaping @MainActor (PlaybackController) -> Void) {
        command.isEnabled = true
        let target = command.addTarget { [weak self] _ in
            Task { @MainActor [weak self] in if let self { action(self) } }
            return .success
        }
        remoteTargets.append((command, target))
    }

    private func updateNowPlaying() {
        guard let song, let asset else { MPNowPlayingInfoCenter.default().nowPlayingInfo = nil; return }
        var info: [String: Any] = [
            MPMediaItemPropertyTitle: song.title,
            MPMediaItemPropertyArtist: song.artist,
            MPMediaItemPropertyAlbumTitle: asset.label,
            MPMediaItemPropertyPlaybackDuration: duration,
            MPNowPlayingInfoPropertyElapsedPlaybackTime: position,
            MPNowPlayingInfoPropertyPlaybackRate: isPlaying ? rate : 0,
            MPNowPlayingInfoPropertyDefaultPlaybackRate: rate,
            MPNowPlayingInfoPropertyMediaType: MPNowPlayingInfoMediaType.audio.rawValue,
            MPNowPlayingInfoPropertyIsLiveStream: false
        ]
        if #available(iOS 18.0, *) { info[MPNowPlayingInfoPropertyExcludeFromSuggestions] = true }
        if let artwork { info[MPMediaItemPropertyArtwork] = artwork }
        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
    }

    private func loadArtwork(_ url: URL?) {
        artworkTask?.cancel()
        let token = generation
        artworkTask = Task { [weak self] in
            guard let self else { return }
            var image = isLocalExercise ? UIImage(named: "FirstPulseCover") : nil
            if let url, APIClient.isSecureRemoteURL(url) {
                if let (data, response) = try? await URLSession.shared.data(from: url),
                   (response as? HTTPURLResponse)?.statusCode == 200, data.count < 8_000_000 {
                    image = UIImage(data: data)
                }
            } else if !isLocalExercise { image = nil }
            guard !Task.isCancelled, token == generation, let image else { return }
            artwork = MPMediaItemArtwork(boundsSize: image.size) { _ in image }
            updateNowPlaying()
        }
    }

    deinit {
        loadTask?.cancel(); artworkTask?.cancel()
        if let periodicObserver { player.removeTimeObserver(periodicObserver) }
        if let boundaryObserver { player.removeTimeObserver(boundaryObserver) }
        notifications.forEach(NotificationCenter.default.removeObserver)
        itemNotifications.forEach(NotificationCenter.default.removeObserver)
        for (command, target) in remoteTargets { command.removeTarget(target) }
    }
}
