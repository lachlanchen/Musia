import SwiftUI
import WatchConnectivity
import WatchKit

@main
struct MusiaWatchApp: App {
    @StateObject private var connection = WatchPlayerConnection()
    @StateObject private var metronome = WatchMetronome()
    @Environment(\.scenePhase) private var phase

    var body: some Scene {
        WindowGroup {
            TabView {
                WatchPlaybackView().environmentObject(connection)
                WatchPracticeView().environmentObject(metronome)
            }
            .tabViewStyle(.verticalPage)
            .tint(.mint)
            .onChange(of: phase) { _, value in
                if value == .active { connection.refresh() }
                else { metronome.stop() }
            }
            .task(id: phase) {
                guard phase == .active else { return }
                while !Task.isCancelled {
                    connection.refresh()
                    do { try await Task.sleep(for: .seconds(5)) } catch { return }
                }
            }
        }
    }
}

@MainActor
final class WatchPlayerConnection: NSObject, ObservableObject, WCSessionDelegate {
    @Published private(set) var snapshot = WatchPlaybackSnapshot()
    @Published private(set) var reachable = false
    @Published private(set) var busy = false
    @Published private(set) var issue: String?

    override init() {
        super.init()
        if WCSession.isSupported() {
            WCSession.default.delegate = self
            WCSession.default.activate()
        }
    }

    func refresh() { send(.refresh) }

    func send(_ action: WatchPlaybackCommand.Action, value: Double? = nil) {
        let session = WCSession.default
        reachable = session.activationState == .activated && session.isReachable
        guard reachable, !busy else { return }
        guard action == .refresh || (snapshot.fresh() && snapshot.ready) else { return }
        let command = WatchPlaybackCommand(action: action, selection: snapshot.selection, value: value)
        guard command.valid(), let data = try? JSONEncoder().encode(command) else { return }
        busy = true; issue = nil
        session.sendMessageData(data, replyHandler: { [weak self] data in
            Task { @MainActor [weak self] in
                self?.busy = false
                self?.receive(data)
            }
        }, errorHandler: { [weak self] _ in
            Task { @MainActor [weak self] in
                self?.busy = false
                self?.issue = "iPhone unavailable"
                self?.reachable = WCSession.default.isReachable
            }
        })
    }

    private func receive(_ data: Data) {
        guard let update = WatchPlaybackSnapshot.decode(data), update.issuedAt >= snapshot.issuedAt else { return }
        snapshot = update; issue = nil
    }

    nonisolated func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        let data = session.receivedApplicationContext["playback"] as? Data
        Task { @MainActor [weak self] in
            if let data { self?.receive(data) }
            self?.refresh()
        }
    }
    nonisolated func sessionReachabilityDidChange(_ session: WCSession) {
        let connected = session.isReachable
        Task { @MainActor [weak self] in self?.reachable = connected; if connected { self?.refresh() } }
    }
    nonisolated func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String: Any]) {
        guard let data = applicationContext["playback"] as? Data else { return }
        Task { @MainActor [weak self] in self?.receive(data) }
    }
    nonisolated func session(_ session: WCSession, didReceiveMessageData messageData: Data) {
        Task { @MainActor [weak self] in self?.receive(messageData) }
    }
}

struct WatchPlaybackView: View {
    @EnvironmentObject private var connection: WatchPlayerConnection
    var body: some View {
        TimelineView(.periodic(from: .now, by: 1)) { context in
            let snapshot = connection.snapshot
            let fresh = snapshot.fresh(at: context.date.timeIntervalSince1970)
            let enabled = fresh && snapshot.ready && connection.reachable && !connection.busy
            ScrollView {
                VStack(spacing: 8) {
                    Text("Musia").font(.headline).foregroundStyle(.mint)
                    Text(fresh && !snapshot.title.isEmpty ? snapshot.title : "Choose a song on iPhone")
                        .font(.body.weight(.semibold)).multilineTextAlignment(.center)
                    Text(fresh ? snapshot.chord ?? "--" : "--")
                        .font(.system(size: 38, weight: .bold, design: .rounded)).minimumScaleFactor(0.5).lineLimit(1)
                        .accessibilityLabel("Chord \(fresh ? snapshot.chord ?? "unavailable" : "unavailable")")
                    if fresh, snapshot.chord != nil {
                        Text(snapshot.chordConfidence).font(.caption2).foregroundStyle(.secondary)
                    }
                    HStack {
                        Text(fresh ? time(snapshot.position) : "0:00").monospacedDigit()
                        Spacer()
                        Text(fresh && snapshot.bpm != nil ? "\(Int(((snapshot.bpm ?? 0) * snapshot.rate).rounded())) BPM" : "BPM --")
                    }.font(.caption2).foregroundStyle(.secondary)
                    HStack(spacing: 12) {
                        Button { connection.send(.seek, value: max(0, snapshot.position - 10)) } label: {
                            Image(systemName: "gobackward.10").font(.title3)
                        }.accessibilityLabel("Back ten seconds")
                        Button { connection.send(snapshot.playing ? .pause : .play) } label: {
                            Image(systemName: snapshot.playing ? "pause.fill" : "play.fill").font(.title2)
                        }.tint(.mint).accessibilityLabel(snapshot.playing ? "Pause on iPhone" : "Play on iPhone")
                        Button { connection.send(.seek, value: min(snapshot.duration, snapshot.position + 10)) } label: {
                            Image(systemName: "goforward.10").font(.title3)
                        }.accessibilityLabel("Forward ten seconds")
                    }.buttonStyle(.bordered).disabled(!enabled)
                    HStack {
                        Button { connection.send(.rate, value: max(0.25, snapshot.rate - 0.25)) } label: { Image(systemName: "minus") }
                            .accessibilityLabel("Slower")
                        Text("\(Int(snapshot.rate * 100))%").monospacedDigit().frame(maxWidth: .infinity)
                        Button { connection.send(.rate, value: min(2, snapshot.rate + 0.25)) } label: { Image(systemName: "plus") }
                            .accessibilityLabel("Faster")
                    }.font(.caption).disabled(!enabled)
                    Text(connection.issue ?? (connection.reachable && fresh ? "On iPhone" : "iPhone offline"))
                        .font(.caption2).foregroundStyle(.secondary)
                    if !fresh && connection.reachable {
                        Button("Reconnect", systemImage: "arrow.clockwise") { connection.refresh() }.disabled(connection.busy)
                    }
                }.padding(.horizontal, 2)
            }
        }
    }
    private func time(_ value: Double) -> String {
        let seconds = Int(max(0, value)); return String(format: "%d:%02d", seconds / 60, seconds % 60)
    }
}

@MainActor
final class WatchMetronome: ObservableObject {
    @Published var bpm = 80 { didSet { if running { restart() } } }
    @Published var beats = 4 { didSet { if running { restart() } } }
    @Published private(set) var running = false
    @Published private(set) var beat = 0
    private var task: Task<Void, Never>?

    func toggle() { running ? stop() : start() }
    func stop() { task?.cancel(); task = nil; running = false; beat = 0 }
    private func restart() { stop(); start() }
    private func start() {
        running = true
        let interval = Duration.seconds(60 / Double(min(200, max(40, bpm))))
        let clock = ContinuousClock()
        task = Task { [weak self] in
            var deadline = clock.now
            while !Task.isCancelled {
                guard let self else { return }
                self.beat = self.beat % self.beats + 1
                WKInterfaceDevice.current().play(self.beat == 1 ? .start : .click)
                deadline += interval
                // Resume from the current clock after a stall; never emit a burst of missed beats.
                if deadline < clock.now { deadline = clock.now + interval }
                do { try await clock.sleep(until: deadline) } catch { return }
            }
        }
    }
    deinit { task?.cancel() }
}

struct WatchPracticeView: View {
    @EnvironmentObject private var metronome: WatchMetronome
    var body: some View {
        ScrollView {
            VStack(spacing: 10) {
                Text("Practice").font(.headline).foregroundStyle(.mint)
                Text("\(metronome.bpm)").font(.system(size: 46, weight: .bold, design: .rounded)).monospacedDigit()
                Text("BPM").font(.caption).foregroundStyle(.secondary)
                Stepper("Tempo", value: $metronome.bpm, in: 40...200, step: 5).labelsHidden()
                    .accessibilityLabel("Tempo \(metronome.bpm) beats per minute")
                HStack(spacing: 8) {
                    ForEach(1...metronome.beats, id: \.self) { index in
                        Circle().fill(metronome.beat == index ? Color.mint : Color.gray.opacity(0.35))
                            .frame(width: 16, height: 16)
                    }
                }.frame(height: 22).accessibilityLabel("Beat \(metronome.beat) of \(metronome.beats)")
                Picker("Beats per bar", selection: $metronome.beats) {
                    ForEach([2, 3, 4, 6], id: \.self) { Text("\($0) beats").tag($0) }
                }.frame(height: 50)
                Button(metronome.running ? "Stop" : "Start", systemImage: metronome.running ? "stop.fill" : "play.fill") {
                    metronome.toggle()
                }.buttonStyle(.borderedProminent)
            }.padding(.horizontal, 2)
        }
        .onDisappear { metronome.stop() }
    }
}
