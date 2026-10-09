import MusiaCore
import SwiftUI

struct CreatorCommunityView: View {
    @EnvironmentObject private var creator: CreatorStore
    @State private var mode = "public"
    @State private var songs: [CreatorSong] = []
    @State private var loading = false
    @State private var issue: String?
    @State private var requestID = UUID()

    var body: some View {
        List {
            Section {
                Picker("Song collection", selection: $mode) {
                    Text("Community").tag("public")
                    Text("My songs").tag("mine")
                    Text("Saved").tag("saved")
                }.pickerStyle(.segmented)
                CreatorAccountLink()
            }
            CreatorNotice()
            if loading { ProgressView("Loading songs…") }
            if let issue { ErrorNotice(message: issue) { Task { await load() } } }
            if mode != "public" && creator.account == nil {
                ContentUnavailableView("Sign in to see your songs", systemImage: "person.crop.circle",
                    description: Text("The public community is available without an account."))
            } else if songs.isEmpty && !loading && issue == nil {
                ContentUnavailableView("No songs yet", systemImage: "music.note",
                    description: Text(mode == "mine" ? "Your completed renders will appear here." : "Refresh to check for available songs."))
            }
            ForEach(songs) { song in
                NavigationLink { CreatorSongView(songID: song.id) } label: {
                    HStack(alignment: .top, spacing: 12) {
                        Image(systemName: song.visibility == .private ? "lock.fill" : "waveform")
                            .font(.title2).foregroundStyle(Palette.teal).frame(width: 36, height: 44)
                            .accessibilityHidden(true)
                        VStack(alignment: .leading, spacing: 5) {
                            Text(song.title).font(.headline)
                            Text(song.author.name).foregroundStyle(.secondary)
                            Text("\(song.language.uppercased()) · \(Timeline.timestamp(song.duration)) · \(song.likes) likes")
                                .font(.caption).foregroundStyle(.secondary)
                            if song.mine { Text("\(song.visibility.rawValue.capitalized) · \(song.moderation)").font(.caption).foregroundStyle(Palette.teal) }
                        }
                    }.padding(.vertical, 6)
                }
            }
        }
        .listStyle(.plain)
        .navigationTitle("Community")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button("Refresh songs", systemImage: "arrow.clockwise") { Task { await load() } }.disabled(loading)
            }
        }
        .refreshable { await load() }
        .task(id: mode) { await load() }
        .onChange(of: creator.identity) { _, _ in
            songs = []; requestID = UUID()
            Task { await load() }
        }
    }
    @MainActor private func load() async {
        let epoch = creator.generation
        let identity = creator.identity
        let selectedMode = mode
        let request = UUID(); requestID = request
        songs = []; issue = nil
        guard selectedMode == "public" || identity != nil else { loading = false; return }
        loading = true
        defer { if requestID == request { loading = false } }
        do {
            // Authenticated public browsing lets the server apply block/reaction state.
            let token = try? creator.snapshot().token
            let response: CreatorSongs = try await creator.api.request("/api/songs?mode=" + selectedMode, token: token)
            guard request == requestID, epoch == creator.generation, identity == creator.identity, selectedMode == mode else { return }
            songs = response.songs
        } catch { if request == requestID && epoch == creator.generation { issue = error.localizedDescription } }
    }
}

struct CreatorSongView: View {
    let songID: String
    @EnvironmentObject private var creator: CreatorStore
    @EnvironmentObject private var player: PlaybackController
    @Environment(\.dismiss) private var dismiss
    @State private var song: CreatorSong?
    @State private var comments: [CreatorComment] = []
    @State private var comment = ""
    @State private var reportReason = "spam"
    @State private var reportDetail = ""
    @State private var reportSheet = false
    @State private var confirmBlock = false
    @State private var confirmVisibility = false
    @State private var loading = false
    @State private var issue: String?
    @State private var commentsIssue: String?
    @State private var requestID = UUID()

    var body: some View {
        List {
            CreatorNotice()
            if loading { ProgressView("Loading song…") }
            if let issue { ErrorNotice(message: issue) { Task { await load() } } }
            if let song {
                Section {
                    Text(song.title).font(.largeTitle.bold()).foregroundStyle(Palette.ink)
                    Label(song.author.name, systemImage: "person.circle")
                    Text("\(song.language.uppercased()) · \(Timeline.timestamp(song.duration))").foregroundStyle(.secondary)
                    Label(song.visibility == .private ? "Private song" : "Public song", systemImage: song.visibility == .private ? "lock" : "globe")
                    if song.mine { LabeledContent("Moderation", value: song.moderation.capitalized) }
                    Button("Open in player", systemImage: "play.circle.fill") { Task { await creator.play(song) } }
                        .buttonStyle(.borderedProminent).disabled(song.audioUrl == nil || creator.busy)
                    Text("Use the player below for playback and timed lyrics.").font(.caption).foregroundStyle(.secondary)
                    if let share = shareURL(song) { ShareLink("Share song", item: share) }
                }
                Section("Community") {
                    ViewThatFits(in: .horizontal) {
                        HStack { reactions(song) }
                        VStack(alignment: .leading, spacing: 12) { reactions(song) }
                    }
                    if creator.account == nil {
                        Text("Sign in to like, save, comment, or report a song.").font(.caption).foregroundStyle(.secondary)
                        CreatorAccountLink()
                    }
                    if song.mine {
                        Button(song.visibility == .private ? "Share publicly…" : "Make private…", systemImage: song.visibility == .private ? "globe" : "lock") {
                            confirmVisibility = true
                        }.disabled(creator.busy)
                    } else {
                        Button("Report song", systemImage: "flag") { reportSheet = true }
                            .disabled(creator.account == nil || creator.busy)
                        Button("Block this account", role: .destructive) { confirmBlock = true }
                            .disabled(creator.account == nil || creator.busy)
                    }
                }
                if !song.lyricLines.isEmpty {
                    Section("Audio lyrics") {
                        Text(song.lyricLines.map(\.text).joined(separator: "\n\n"))
                            .textSelection(.enabled).fixedSize(horizontal: false, vertical: true)
                    }
                }
                Section("Comments") {
                    if let commentsIssue { Text(commentsIssue).foregroundStyle(Palette.coral) }
                    if comments.isEmpty { Text("No comments loaded.").foregroundStyle(.secondary) }
                    ForEach(comments) { entry in
                        VStack(alignment: .leading, spacing: 6) {
                            Text(entry.author).font(.headline)
                            Text(entry.text).textSelection(.enabled)
                            if entry.state != "published" { Text(entry.state.capitalized).font(.caption).foregroundStyle(.secondary) }
                            if entry.mine {
                                Button("Delete comment", role: .destructive) {
                                    Task { await mutate("/api/comments/\((try? CreatorAPI.segment(entry.id)) ?? "")", method: "DELETE") }
                                }.font(.caption).disabled(creator.busy)
                            }
                        }.padding(.vertical, 4)
                    }
                    if creator.account != nil {
                        CreatorTextField(title: "Write a respectful comment", text: $comment, lines: 2...5)
                        Button("Post comment", systemImage: "paperplane") {
                            Task {
                                let text = comment.trimmingCharacters(in: .whitespacesAndNewlines)
                                if await mutate(songPath + "/comments", fields: ["text": text]) { comment = "" }
                            }
                        }.disabled(comment.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || comment.count > 2000 || creator.busy)
                    }
                }
            }
        }
        .listStyle(.plain)
        .navigationTitle("Song")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button("Refresh song", systemImage: "arrow.clockwise") { Task { await load() } }.disabled(loading)
            }
        }
        .task(id: creator.identity) {
            song = nil; comments = []; comment = ""; reportDetail = ""
            reportSheet = false; confirmBlock = false; confirmVisibility = false
            await load()
        }
        .sheet(isPresented: $reportSheet) { reportForm }
        .confirmationDialog("Block this account?", isPresented: $confirmBlock, titleVisibility: .visible) {
            Button("Block account", role: .destructive) {
                if let song { Task {
                    if await mutate("/api/accounts/\((try? CreatorAPI.segment(song.author.id)) ?? "")/block", active: true) {
                        player.clearCreatorSelection()
                        dismiss()
                    }
                } }
            }
        } message: { Text("Musia will hide this account's content. You can undo this from Blocked accounts in Settings.") }
        .confirmationDialog(song?.visibility == .private ? "Share this song publicly?" : "Make this song private?", isPresented: $confirmVisibility, titleVisibility: .visible) {
            Button(song?.visibility == .private ? "Submit for public sharing" : "Make private") {
                Task { await mutate(songPath + "/visibility", fields: ["visibility": song?.visibility == .private ? "public" : "private"]) }
            }
        } message: { Text("Public sharing enters moderation. Private songs are available only to their owner.") }
    }
    @ViewBuilder private func reactions(_ song: CreatorSong) -> some View {
        Button("\(song.liked ? "Unlike" : "Like") · \(song.likes)", systemImage: song.liked ? "heart.fill" : "heart") {
            Task { await mutate(songPath + "/reactions/like", active: !song.liked) }
        }.disabled(creator.account == nil || creator.busy)
        Button(song.saved ? "Unsave" : "Save", systemImage: song.saved ? "bookmark.fill" : "bookmark") {
            Task { await mutate(songPath + "/reactions/save", active: !song.saved) }
        }.disabled(creator.account == nil || creator.busy)
    }
    private var reportForm: some View {
        NavigationStack {
            Form {
                Section("Reason for reporting") {
                    Picker("Reason", selection: $reportReason) {
                        Text("Spam").tag("spam"); Text("Harassment or abuse").tag("harassment")
                        Text("Rights or copyright").tag("copyright"); Text("Other").tag("other")
                    }
                    CreatorTextField(title: "Additional details (optional)", text: $reportDetail, lines: 3...8)
                    Button("Send report") {
                        Task {
                            if await mutate(songPath + "/reports", fields: ["reason": reportReason + (reportDetail.isEmpty ? "" : ": " + reportDetail)]) {
                                creator.notice = "Your report was sent for review."; reportSheet = false; reportDetail = ""
                            }
                        }
                    }.disabled(creator.busy || reportDetail.count > 2000)
                    if let notice = creator.notice { Text(notice).foregroundStyle(Palette.coral) }
                }
            }.formStyle(.grouped)
                .navigationTitle("Report song")
                .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Cancel") { reportSheet = false } } }
        }
#if os(macOS)
        .frame(minWidth: 440, minHeight: 350)
#endif
    }
    private var songPath: String { "/api/songs/\((try? CreatorAPI.segment(songID)) ?? "")" }
    private func shareURL(_ song: CreatorSong) -> URL? {
        guard song.visibility == .public, song.moderation == "approved", let path = song.sharePath else { return nil }
        return try? CreatorAPI.mediaURL(path)
    }
    @MainActor private func load() async {
        let epoch = creator.generation; let identity = creator.identity
        let request = UUID(); requestID = request; loading = true; issue = nil; commentsIssue = nil
        defer { if request == requestID { loading = false } }
        do {
            let token = try? creator.snapshot().token
            let loaded: CreatorSong = try await creator.api.request(songPath, token: token)
            guard epoch == creator.generation, identity == creator.identity, request == requestID else { return }
            guard loaded.id == songID else { throw ContractError.invalid("song identifier") }
            song = loaded
            do {
                let result: CreatorComments = try await creator.api.request(songPath + "/comments", token: token)
                guard epoch == creator.generation, identity == creator.identity, request == requestID else { return }
                comments = result.comments
            } catch { if epoch == creator.generation && request == requestID { commentsIssue = error.localizedDescription } }
        } catch {
            if epoch == creator.generation && request == requestID { song = nil; comments = []; issue = error.localizedDescription }
        }
    }
    @MainActor @discardableResult private func mutate(_ path: String, method: String = "POST", fields: [String: String]? = nil, active: Bool? = nil) async -> Bool {
        var succeeded = false
        await creator.perform {
            let captured = try creator.snapshot()
            let data = try active.map { try CreatorAPI.body(["active": $0]) } ?? CreatorAPI.body(fields ?? [:])
            _ = try await creator.api.send(path, method: method, token: captured.token, body: data)
            try creator.requireCurrent(captured)
            succeeded = true
            await load()
        }
        return succeeded
    }
}

struct CreatorBlocksView: View {
    @EnvironmentObject private var creator: CreatorStore
    @State private var blocks: [CreatorAuthor] = []
    @State private var issue: String?
    var body: some View {
        List {
            CreatorNotice()
            if let issue { ErrorNotice(message: issue) { Task { await load() } } }
            if blocks.isEmpty { Text("No blocked accounts loaded.").foregroundStyle(.secondary) }
            ForEach(blocks, id: \.id) { account in
                HStack {
                    Text(account.name); Spacer()
                    Button("Unblock") { Task {
                        await creator.perform {
                            let captured = try creator.snapshot()
                            _ = try await creator.api.send("/api/accounts/\(CreatorAPI.segment(account.id))/block", token: captured.token,
                                body: CreatorAPI.body(["active": false]))
                            try creator.requireCurrent(captured); await load()
                        }
                    } }.disabled(creator.busy)
                }
            }
        }.navigationTitle("Blocked accounts")
            .task(id: creator.identity) { blocks = []; await load() }
    }
    @MainActor private func load() async {
        guard let captured = try? creator.snapshot() else { return }
        do {
            let response: CreatorBlocks = try await creator.api.request("/api/blocks", token: captured.token)
            try creator.requireCurrent(captured); blocks = response.blocks; issue = nil
        } catch { if creator.identity == captured.identity { issue = error.localizedDescription } }
    }
}
