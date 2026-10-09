import Combine
import Foundation
import MusiaCore

@MainActor
final class CreatorStore: ObservableObject {
    struct SessionSnapshot {
        let identity: CreatorIdentity
        let token: String
    }
    private struct Credential: Codable { let token: String; let expiresAt: Date }
    @Published private(set) var capabilities: CreatorCapabilities?
    @Published private(set) var account: CreatorAccount?
    @Published private(set) var jobs: [CreatorJob] = []
    @Published private(set) var pending: PendingCreatorRender?
    @Published private(set) var busy = false
    @Published private(set) var refreshing = false
    @Published private(set) var hasSession = false
    @Published var notice: String?
    @Published var brief = CreatorBrief() {
        didSet {
            if agentBusy {
                for key in Self.textFields where oldValue[keyPath: key] != brief[keyPath: key] { editedText.insert(key) }
                if oldValue.bpm != brief.bpm { editedTempo = true }
                if oldValue.duration != brief.duration { editedDuration = true }
            }
            saveWorkspace()
        }
    }
    @Published private(set) var agentMessage: String?
    @Published private(set) var conversation: [CreatorChatMessage] = []
    @Published private(set) var agentBusy = false
    @Published var agentInput = ""
    private struct Workspace: Codable { let brief: CreatorBrief; let messages: [CreatorChatMessage] }
    private var workspaces: [String: Workspace] = [:]
    private var workspaceReady = false
    private var loadingWorkspace = false
    private static let textFields: [WritableKeyPath<CreatorBrief, String>] = [\.title, \.idea, \.lyrics, \.caption, \.language, \.key]
    private var editedText = Set<WritableKeyPath<CreatorBrief, String>>()
    private var editedTempo = false
    private var editedDuration = false
    @Published private(set) var generation = UUID()
    let api = CreatorAPI()
    let authentication = CreatorAuthentication()
    private var credential: Credential?
    private var initialized = false
    private var pendingStorageReady = false
    private var pendingByOwner: [String: PendingCreatorRender] = [:]
    private var pendingRevocations: [String] = []
    private var revoking = false
    private weak var player: PlaybackController?
    private var mediaGeneration = UUID()
    private var cachedAudio: URL?
    private let mediaDirectory = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
        .appendingPathComponent("MusiaCreatorAudio", isDirectory: true)

    var identity: CreatorIdentity? {
        account.map { CreatorIdentity(owner: $0.id, generation: generation) }
    }
    var canRender: Bool {
        capabilities?.generation == true && account?.termsAccepted == true
        && (capabilities?.invitationRequired == false || account?.invited == true)
        && (account?.usage.remaining ?? 0) > 0 && pending == nil && pendingStorageReady
    }
    func snapshot() throws -> SessionSnapshot {
        guard let identity, let credential, credential.expiresAt > Date() else { throw CreatorError.signInRequired }
        return SessionSnapshot(identity: identity, token: credential.token)
    }
    func requireCurrent(_ snapshot: SessionSnapshot) throws {
        guard snapshot.identity.accepts(identity), snapshot.token == credential?.token else { throw CreatorError.sessionChanged }
    }

    func start(player: PlaybackController) async {
        self.player = player
        guard !initialized else { return }
        initialized = true
        try? FileManager.default.removeItem(at: mediaDirectory)
        do {
            pendingByOwner = try CreatorKeychain.read([String: PendingCreatorRender].self, key: "pending-renders") ?? [:]
            workspaces = try CreatorKeychain.read([String: Workspace].self, key: "creator-workspaces") ?? [:]
            workspaceReady = true
            pendingStorageReady = true
            pendingRevocations = try CreatorKeychain.read([String].self, key: "pending-revocations") ?? []
            credential = try CreatorKeychain.read(Credential.self, key: "session")
            if let credential, credential.expiresAt <= Date() {
                try CreatorKeychain.remove("session"); self.credential = nil
            }
            hasSession = credential != nil
        } catch { notice = error.localizedDescription }
        await refresh()
    }

    func refresh() async {
        guard !refreshing else { return }
        refreshing = true
        let epoch = generation
        defer { if epoch == generation { refreshing = false } }
        await revokePendingSessions()
        do {
            let loaded: CreatorCapabilities = try await api.request("/api/capabilities")
            guard epoch == generation else { return }
            capabilities = loaded
        } catch { if epoch == generation { capabilities = nil; notice = error.localizedDescription } }
        guard let credential, epoch == generation else { return }
        do {
            let me: CreatorMe = try await api.request("/api/me", token: credential.token)
            guard epoch == generation else { return }
            guard let next = me.account else { try clearSession(); return }
            if let previous = account, previous.id != next.id { try clearSession(); return }
            let firstLoad = account == nil
            account = next
            if firstLoad {
                loadingWorkspace = true
                brief = workspaces[next.id]?.brief ?? CreatorBrief()
                conversation = CreatorChatMessage.bounded(workspaces[next.id]?.messages ?? [])
                loadingWorkspace = false
            }
            pending = pendingByOwner[next.id]
            await refreshJobs()
        } catch CreatorError.server(401, _) {
            guard epoch == generation else { return }
            do { try clearSession() } catch { notice = error.localizedDescription }
            notice = "Your session expired. Sign in to reconnect your account."
        } catch { if epoch == generation { notice = error.localizedDescription } }
    }

    func signIn() async {
        guard !busy, credential == nil, capabilities?.login == true else { return }
        busy = true; notice = nil
        let epoch = generation
        defer { if epoch == generation { busy = false } }
        do {
            let response = try await authentication.signIn(api: api)
            guard epoch == generation else { return }
            let next = Credential(token: response.token, expiresAt: Date().addingTimeInterval(response.expiresIn))
            try CreatorKeychain.write(next, key: "session")
            credential = next; hasSession = true
            await refresh()
        } catch is CancellationError { }
        catch { if epoch == generation { notice = error.localizedDescription } }
    }

    func refreshJobs() async {
        guard let captured = try? snapshot() else { return }
        do {
            let result: CreatorJobs = try await api.request("/api/jobs", token: captured.token)
            try requireCurrent(captured); jobs = result.jobs
        } catch { if captured.identity == identity { notice = error.localizedDescription } }
    }

    func accountAction(_ path: String, body: Data = Data("{}".utf8)) async {
        await perform {
            let captured = try self.snapshot()
            _ = try await self.api.send(path, token: captured.token, body: body)
            try self.requireCurrent(captured)
            await self.refresh()
        }
    }
    func askAgent(_ message: String) async {
        guard capabilities?.agent == true else { return }
        await perform {
            let captured = try self.snapshot()
            let original = self.brief
            let body = try CreatorAgentRequest(message: message, brief: original, history: self.conversation).boundedBody()
            self.conversation = CreatorChatMessage.bounded(self.conversation + [CreatorChatMessage(role: "user", content: message)])
            self.agentInput = ""; self.agentBusy = true
            self.editedText.removeAll(); self.editedTempo = false; self.editedDuration = false
            self.saveWorkspace()
            defer { if captured.identity == self.identity { self.agentBusy = false } }
            let reply: CreatorAgentReply = try await self.api.request("/api/agent", method: "POST", token: captured.token,
                body: body)
            try self.requireCurrent(captured)
            guard reply.brief.isValidDraft, !reply.message.isEmpty, reply.message.unicodeScalars.count <= 1600 else {
                throw CreatorError.unavailable("The agent returned an invalid draft. Your edits are preserved.")
            }
            var merged = reply.brief
            for key in self.editedText { merged[keyPath: key] = self.brief[keyPath: key] }
            if self.editedTempo { merged.bpm = self.brief.bpm }
            if self.editedDuration { merged.duration = self.brief.duration }
            self.agentBusy = false
            self.conversation = CreatorChatMessage.bounded(self.conversation + [CreatorChatMessage(role: "assistant", content: reply.message)])
            self.brief = merged; self.agentMessage = reply.message
            self.saveWorkspace()
        }
    }

    private func saveWorkspace() {
        guard workspaceReady, !loadingWorkspace, let owner = account?.id else { return }
        workspaces[owner] = Workspace(brief: brief, messages: conversation)
        do { try CreatorKeychain.write(workspaces, key: "creator-workspaces") }
        catch { notice = "Your draft could not be saved securely. Keep this screen open and try again." }
    }

    func render(visibility: CreatorVisibility) async {
        guard canRender, brief.isRenderable else { return }
        await perform {
            let captured = try self.snapshot()
            let pending = PendingCreatorRender(owner: captured.identity.owner,
                request: CreatorRenderRequest(brief: self.brief, visibility: visibility))
            // Securely save BEFORE transmission, including the exact frozen request.
            var next = self.pendingByOwner; next[pending.owner] = pending
            try CreatorKeychain.write(next, key: "pending-renders")
            self.pendingByOwner = next; self.pending = pending
            try await self.submit(pending, captured: captured, initial: true)
        }
    }
    func reconnectRender() async {
        guard let pending, pending.canRetry(owner: account?.id) else { return }
        await perform { try await self.submit(pending, captured: self.snapshot(), initial: false) }
    }
    private func submit(_ pending: PendingCreatorRender, captured: SessionSnapshot, initial: Bool) async throws {
        guard pending.canRetry(owner: captured.identity.owner) else { throw CreatorError.sessionChanged }
        let receipt: CreatorJobReceipt
        do {
            receipt = try await api.request("/api/jobs", method: "POST", token: captured.token,
                body: CreatorAPI.body(pending.request), idempotencyKey: pending.key)
        } catch {
            try requireCurrent(captured)
            // A retry's 422 cannot disprove an earlier unknown acceptance.
            if pending.canDiscard(after: error, initial: initial) {
                try clearPending(pending, captured: captured)
            }
            throw error
        }
        try clearPending(pending, captured: captured)
        jobs.removeAll { $0.id == receipt.job.id }; jobs.insert(receipt.job, at: 0)
        notice = "Render request received. Refresh jobs to follow its progress."
        await refresh()
    }
    private func clearPending(_ pending: PendingCreatorRender, captured: SessionSnapshot) throws {
        try requireCurrent(captured)
        guard pendingByOwner[pending.owner] == pending, self.pending == pending else {
            throw CreatorError.sessionChanged
        }
        var next = pendingByOwner; next.removeValue(forKey: pending.owner)
        try CreatorKeychain.write(next, key: "pending-renders")
        pendingByOwner = next; self.pending = nil
    }
    func cancel(_ job: CreatorJob) async {
        guard job.canCancel else { return }
        await accountAction("/api/jobs/\((try? CreatorAPI.segment(job.id)) ?? "")/cancel")
    }

    func logout() async {
        guard !busy else { return }
        do {
            if let token = credential?.token {
                var next = pendingRevocations
                if !next.contains(token) { next.append(token) }
                try CreatorKeychain.write(next, key: "pending-revocations")
                pendingRevocations = next
            }
            try clearSession()
        } catch { notice = error.localizedDescription; return }
        let epoch = generation
        await revokePendingSessions()
        if epoch == generation && !pendingRevocations.isEmpty {
            notice = "Signed out on this device. Server sign-out is awaiting a connection and will retry when you refresh."
        }
    }
    private func revokePendingSessions() async {
        guard !revoking else { return }
        revoking = true; defer { revoking = false }
        for token in pendingRevocations {
            do {
                do { _ = try await api.send("/auth/logout", token: token) }
                catch CreatorError.server(401, _) { /* Already revoked or expired. */ }
                let next = pendingRevocations.filter { $0 != token }
                try CreatorKeychain.write(next, key: "pending-revocations")
                pendingRevocations = next
            } catch { return }
        }
    }
    func deleteAccount() async {
        await perform {
            let captured = try self.snapshot()
            _ = try await self.api.send("/api/me", method: "DELETE", token: captured.token)
            try self.requireCurrent(captured)
            var retained = self.pendingByOwner
            retained.removeValue(forKey: captured.identity.owner)
            try CreatorKeychain.write(retained, key: "pending-renders")
            self.pendingByOwner = retained
            self.workspaces.removeValue(forKey: captured.identity.owner)
            try CreatorKeychain.write(self.workspaces, key: "creator-workspaces")
            try self.clearSession()
            self.notice = "Your creator account was deleted. Apple subscriptions are managed separately in the App Store."
        }
    }
    private func clearSession() throws {
        // If Keychain is locked, do not pretend durable logout succeeded.
        try CreatorKeychain.remove("session")
        authentication.cancel()
        generation = UUID(); mediaGeneration = UUID()
        credential = nil; hasSession = false; account = nil; jobs = []; pending = nil
        agentBusy = false; conversation = []; agentInput = ""
        brief = CreatorBrief(); agentMessage = nil; busy = false; refreshing = false
        player?.clearCreatorSelection()
        cachedAudio = nil
        try? FileManager.default.removeItem(at: mediaDirectory)
        // Pending renders remain protected and bound to their original owner.
    }

    func play(_ song: CreatorSong) async {
        await perform {
            guard let source = song.audioUrl else { throw CreatorError.unavailable("Audio is not ready yet.") }
            guard let player = self.player else { throw CreatorError.unavailable("The player is not ready yet.") }
            let url = try CreatorAPI.mediaURL(source)
            let epoch = self.generation
            let playbackGeneration = player.selectionGeneration
            let mediaEpoch = UUID(); self.mediaGeneration = mediaEpoch
            var stagedAudio: URL?
            defer {
                if let stagedAudio { try? FileManager.default.removeItem(at: stagedAudio) }
            }
            let playbackURL: URL
            if song.requiresAuthenticatedPlayback {
                let captured = try self.snapshot()
                let download = try await self.api.downloadAudio(url, token: captured.token)
                defer { try? FileManager.default.removeItem(at: download.file) }
                try self.requireCurrent(captured)
                guard mediaEpoch == self.mediaGeneration else { throw CancellationError() }
                try FileManager.default.createDirectory(at: self.mediaDirectory, withIntermediateDirectories: true,
                    attributes: [.posixPermissions: 0o700])
                playbackURL = self.mediaDirectory.appendingPathComponent(UUID().uuidString)
                    .appendingPathExtension(download.suffix)
                try FileManager.default.moveItem(at: download.file, to: playbackURL)
                stagedAudio = playbackURL
                try FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: playbackURL.path)
#if os(iOS)
                // Allow the existing background audio transport after first unlock.
                try FileManager.default.setAttributes([.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication], ofItemAtPath: playbackURL.path)
#endif
            } else { playbackURL = url }
            try Task.checkCancellation()
            guard epoch == self.generation else { throw CreatorError.sessionChanged }
            guard playbackGeneration == player.selectionGeneration else { throw CancellationError() }
            player.openCreator(try song.playbackSong(audioURL: playbackURL))
            let previous = self.cachedAudio
            self.cachedAudio = stagedAudio
            stagedAudio = nil
            if let previous { try? FileManager.default.removeItem(at: previous) }
        }
    }

    /// Common action boundary. Every request still captures an identity before its
    /// first await; late errors cannot overwrite the next account's presentation.
    func perform(_ work: () async throws -> Void) async {
        guard !busy else { return }
        let epoch = generation
        busy = true; notice = nil
        defer { if epoch == generation { busy = false } }
        do { try await work() }
        catch is CancellationError { }
        catch { if epoch == generation { notice = error.localizedDescription } }
    }
}
