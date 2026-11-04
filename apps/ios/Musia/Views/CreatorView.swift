import MusiaCore
import SwiftUI

struct CreatorTextField: View {
    let title: String
    @Binding var text: String
    var lines: ClosedRange<Int> = 1...1
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title).font(.subheadline.weight(.medium))
            TextField(title, text: $text, axis: .vertical).lineLimit(lines)
                .textFieldStyle(.roundedBorder).accessibilityLabel(title)
        }.padding(.vertical, 3)
    }
}

struct CreatorNotice: View {
    @EnvironmentObject private var creator: CreatorStore
    var body: some View {
        if let notice = creator.notice {
            Section {
                VStack(alignment: .leading, spacing: 8) {
                    Label(notice, systemImage: "info.circle")
                        .foregroundStyle(Palette.coral).fixedSize(horizontal: false, vertical: true)
                    Button("Dismiss") { creator.notice = nil }.font(.caption)
                }
                .accessibilityElement(children: .contain)
            }
        }
    }
}

struct CreatorAccountLink: View {
    @EnvironmentObject private var creator: CreatorStore
    var body: some View {
        NavigationLink { CreatorAccountView() } label: {
            Label(creator.account?.name ?? "Account & subscriptions", systemImage: "person.crop.circle")
        }
    }
}

struct CreatorView: View {
    @EnvironmentObject private var creator: CreatorStore
    @Environment(\.scenePhase) private var scenePhase
    @State private var mode = "Agent"
    @State private var rights = false
    @State private var visibility = CreatorVisibility.private
    @State private var confirmRender = false
    @State private var confirmCancel: CreatorJob?
    @State private var renderExpanded = false
    @State private var jobsExpanded = false
    @State private var contextOpen = false

    var body: some View {
        Group {
            if mode == "Agent" { chatWorkspace }
            else { editor }
        }
        .navigationTitle(mode == "Agent" ? "Musia" : "Song details")
        .toolbar {
            ToolbarItem(placement: .automatic) {
                Button { mode = mode == "Agent" ? "Studio" : "Agent" } label: {
                    Label(mode == "Agent" ? "Song details" : "Chat", systemImage: mode == "Agent" ? "slider.horizontal.3" : "bubble.left.and.bubble.right")
                }.accessibilityIdentifier("creator.workspace")
            }
            ToolbarItem(placement: .automatic) { CreatorAccountLink() }
        }
        .safeAreaInset(edge: .bottom, spacing: 0) {
            if mode == "Agent" { composer }
        }
        .task(id: creator.identity) {
            await creator.refreshJobs()
            while !Task.isCancelled {
                do { try await Task.sleep(nanoseconds: 15_000_000_000) } catch { return }
                if scenePhase == .active && creator.account != nil { await creator.refreshJobs() }
            }
        }
        .onChange(of: scenePhase) { _, phase in if phase == .active { Task { await creator.refresh() } } }
        .onChange(of: creator.identity) { _, _ in
            rights = false; mode = "Agent"; renderExpanded = false; jobsExpanded = false
        }
        .onChange(of: creator.brief) { _, _ in rights = false }
        .sheet(isPresented: $contextOpen) {
            NavigationStack {
                Form { contextControls }
                    .navigationTitle("Song reference")
                    .toolbar { Button("Done") { contextOpen = false } }
            }
        }
        .sheet(isPresented: $confirmRender) {
            NavigationStack {
                Form {
                    Section(creator.brief.title) {
                        Text("\(creator.brief.duration) seconds · 1 render")
                        Picker("Visibility", selection: $visibility) {
                            Text("Only me").tag(CreatorVisibility.private)
                            Text("Public after review").tag(CreatorVisibility.public)
                        }
                        Toggle("I have permission to use these lyrics, music and any voice likeness.", isOn: $rights)
                        Button("Generate song", systemImage: "waveform.badge.plus") {
                            confirmRender = false
                            Task { if rights { await creator.render(visibility: visibility) } }
                        }.buttonStyle(.borderedProminent)
                            .disabled(!rights || !creator.canRender || creator.busy || !creator.brief.isRenderable)
                        if !creator.canRender { Text(renderAvailability).font(.footnote) }
                    }
                }.navigationTitle("Create this song")
                    .toolbar { Button("Cancel") { confirmRender = false } }
            }
        }
        .confirmationDialog("Cancel this queued render?", isPresented: Binding(get: { confirmCancel != nil }, set: { if !$0 { confirmCancel = nil } }), titleVisibility: .visible) {
            Button("Cancel render", role: .destructive) {
                if let job = confirmCancel { Task { await creator.cancel(job) } }; confirmCancel = nil
            }
        }
    }

    private var chatWorkspace: some View {
        ScrollViewReader { scroll in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 26) {
                    if creator.conversation.isEmpty {
                        VStack(alignment: .leading, spacing: 14) {
                            Image(systemName: "waveform").font(.system(size: 32)).foregroundStyle(Palette.coral)
                            Text("What shall we make?").font(.title2.weight(.semibold))
                        }.padding(.top, 36).padding(.bottom, 20)
                    }
                    ForEach(Array(creator.conversation.enumerated()), id: \.offset) { _, item in
                        let user = item.role == "user"
                        HStack(alignment: .top, spacing: 14) {
                            if user { Spacer(minLength: 32) }
                            Text(item.content).font(.system(size: 18)).lineSpacing(5)
                                .textSelection(.enabled).fixedSize(horizontal: false, vertical: true)
                                .padding(user ? 14 : 0)
                                .background(user ? Palette.coral.opacity(0.10) : Color.clear, in: RoundedRectangle(cornerRadius: 8))
                            if !user { Spacer(minLength: 12) }
                        }.accessibilityLabel("\(user ? "You" : "Musia"): \(item.content)")
                    }
                    if creator.agentBusy {
                        HStack(spacing: 10) { ProgressView(); Text("Musia is working…").foregroundStyle(.secondary) }
                            .accessibilityIdentifier("creator.working")
                    }
                    if let notice = creator.notice {
                        Label(notice, systemImage: "info.circle").font(.footnote).foregroundStyle(.secondary)
                    }
                    if creator.brief.isRenderable && !creator.agentBusy {
                        VStack(alignment: .leading, spacing: 10) {
                            Text(creator.brief.title).font(.headline)
                            HStack {
                                Button("Generate song", systemImage: "waveform.badge.plus") { rights = false; confirmRender = true }
                                    .buttonStyle(.borderedProminent).disabled(creator.busy)
                                    .accessibilityIdentifier("creator.render")
                                Button("Edit", systemImage: "pencil") { mode = "Studio" }
                            }
                        }.padding(.vertical, 8)
                    }
                    if let pending = creator.pending {
                        Button("Reconnect: \(pending.request.brief.title)", systemImage: "arrow.clockwise") {
                            Task { await creator.reconnectRender() }
                        }.disabled(creator.busy)
                    }
                    ForEach(creator.jobs) { job in
                        VStack(alignment: .leading, spacing: 6) {
                            Label(job.title ?? "Song", systemImage: job.status == "ready" ? "music.note" : "clock")
                            Text(job.status.replacingOccurrences(of: "_", with: " ").capitalized).font(.footnote).foregroundStyle(.secondary)
                            if let songID = job.songId { NavigationLink("Listen") { CreatorSongView(songID: songID) } }
                        }
                    }
                    Color.clear.frame(height: 1).id("chat-end")
                }.frame(maxWidth: 760).padding(20).frame(maxWidth: .infinity)
            }
            .onChange(of: creator.conversation.count) { _, _ in withAnimation { scroll.scrollTo("chat-end", anchor: .bottom) } }
            .onChange(of: creator.agentBusy) { _, _ in withAnimation { scroll.scrollTo("chat-end", anchor: .bottom) } }
        }
    }

    private var contextControls: some View {
        Section {
            Picker("Focus", selection: $creator.agentFocus) {
                Text("Create").tag("create"); Text("Analyze").tag("analyze"); Text("Learn").tag("learn")
            }.pickerStyle(.segmented)
            Picker("Song", selection: $creator.referenceKey) {
                Text("No song selected").tag("")
                ForEach(creator.referenceCatalog) { Text($0.title).tag("catalog:" + $0.id) }
                ForEach(creator.jobs.filter { $0.status == "ready" }) { Text($0.title ?? "My song").tag("created:" + $0.id) }
            }
            if !creator.referenceKey.isEmpty {
                Stepper("From: \(Int(creator.referencePosition)) seconds", value: $creator.referencePosition, in: 0...21600, step: 5)
            }
        }.disabled(creator.busy)
    }

    private var editor: some View {
        Form {
            CreatorNotice()
            if let pending = creator.pending {
                Section("Render awaiting confirmation") {
                    Text(pending.request.brief.title).font(.headline)
                    Text("The previous request may already be running. Reconnect checks the same request without creating a new render.")
                        .foregroundStyle(.secondary)
                    Button("Reconnect render request", systemImage: "arrow.clockwise") {
                        Task { await creator.reconnectRender() }
                    }.disabled(creator.busy)
                }
            }
            Section("Song brief") {
                CreatorTextField(title: "Title", text: $creator.brief.title)
                CreatorTextField(title: "Idea", text: $creator.brief.idea, lines: 2...5)
                Picker("Vocal language", selection: $creator.brief.language) {
                    Text("English").tag("en"); Text("中文").tag("zh")
                    Text("日本語").tag("ja"); Text("Mixed languages").tag("mixed")
                }
                VStack(alignment: .leading, spacing: 6) {
                    Text("Lyrics").font(.headline)
                    TextEditor(text: $creator.brief.lyrics).frame(minHeight: 180)
                        .accessibilityLabel("Editable lyrics")
                }
                CreatorTextField(title: "Arrangement and vocal direction", text: $creator.brief.caption, lines: 3...6)
                Stepper("Duration: \(creator.brief.duration) seconds", value: $creator.brief.duration, in: 30...180, step: 5)
                Stepper("Tempo: \(creator.brief.bpm) BPM", value: $creator.brief.bpm, in: 40...200)
                CreatorTextField(title: "Musical key", text: $creator.brief.key)
            }.disabled(creator.busy && !creator.agentBusy)
            Section {
              DisclosureGroup("Create your song", isExpanded: $renderExpanded) {
                if let account = creator.account {
                    LabeledContent("Remaining this period", value: "\(account.usage.remaining) of \(account.usage.limit)")
                }
                Button("Generate song", systemImage: "waveform.badge.plus") { rights = false; confirmRender = true }
                    .buttonStyle(.borderedProminent)
                    .disabled(!creator.brief.isRenderable || creator.busy)
                    .accessibilityIdentifier("creator.render")
                if !creator.canRender {
                    Text(renderAvailability).font(.caption).foregroundStyle(.secondary)
                }
              }
            }
            Section {
              DisclosureGroup("Your songs and jobs", isExpanded: $jobsExpanded) {
                Button("Refresh job status", systemImage: "arrow.clockwise") { Task { await creator.refresh() } }
                    .disabled(creator.refreshing || creator.account == nil)
                if creator.jobs.isEmpty { Text("No jobs loaded yet.").foregroundStyle(.secondary) }
                ForEach(creator.jobs) { job in
                    VStack(alignment: .leading, spacing: 8) {
                        Text(job.title ?? "Song render").font(.headline)
                        Label(job.status.capitalized, systemImage: job.status == "ready" ? "checkmark.circle" : (job.isTerminal ? "exclamationmark.circle" : "clock"))
                        if let message = job.message { Text(message).font(.caption).foregroundStyle(.secondary) }
                        if let songID = job.songId {
                            NavigationLink("Open song") { CreatorSongView(songID: songID) }
                        }
                        if job.canCancel {
                            Button("Cancel queued render", role: .destructive) { confirmCancel = job }
                                .disabled(creator.busy)
                        }
                    }.padding(.vertical, 4)
                }
              }
            }
        }
        .formStyle(.grouped)
    }
    private var composer: some View {
        VStack(alignment: .leading, spacing: 8) {
            if creator.account == nil {
                NavigationLink("Sign in to chat") { CreatorAccountView() }
                    .font(.subheadline)
            }
            HStack(alignment: .bottom, spacing: 12) {
                if creator.supportsSongContext {
                    Button { contextOpen = true } label: { Image(systemName: "plus").frame(width: 32, height: 40) }
                        .accessibilityLabel("Song reference and focus")
                }
                TextField("Message Musia", text: $creator.agentInput, axis: .vertical)
                    .lineLimit(1...6).textFieldStyle(.plain).font(.system(size: 18)).padding(.vertical, 10)
                    .accessibilityLabel("Message Musia")
                Button {
                    let input = creator.agentInput
                    Task { await creator.askAgent(input) }
                } label: {
                    Image(systemName: "arrow.up").font(.headline).frame(width: 28, height: 32)
                }
                .buttonStyle(.borderedProminent).accessibilityLabel("Send")
                .disabled(creator.busy || creator.account == nil || creator.capabilities?.agent != true || creator.agentInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }.padding(10).background(Palette.coral.opacity(0.06), in: RoundedRectangle(cornerRadius: 8))
        }.padding(.horizontal, 16).padding(.vertical, 10).frame(maxWidth: 800).frame(maxWidth: .infinity).background(.regularMaterial)
    }
    private var renderAvailability: String {
        if creator.account == nil { return "Sign in from Account & subscriptions to render." }
        if creator.account?.termsAccepted != true { return "Accept the current creator terms from your account." }
        if creator.capabilities?.invitationRequired == true && creator.account?.invited != true { return "Redeem your invitation from your account." }
        if creator.pending != nil { return "Reconnect your previous request before starting another render." }
        if creator.account?.usage.remaining == 0 { return "Your current render allowance is used. Check your account for usage and plans." }
        return "Rendering is unavailable. Refresh your account to check service access."
    }
}
