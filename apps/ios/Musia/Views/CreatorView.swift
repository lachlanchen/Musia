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
    @State private var message = ""
    @State private var rights = false
    @State private var visibility = CreatorVisibility.private
    @State private var confirmRender = false
    @State private var confirmCancel: CreatorJob?

    var body: some View {
        Form {
            Section {
                Label("Make room for your next song", systemImage: "sparkles")
                    .font(.title2.bold()).foregroundStyle(Palette.teal)
                Text("Shape an idea with the assistant, edit the brief, then choose when to render.")
                    .foregroundStyle(.secondary)
                CreatorAccountLink()
                if let account = creator.account {
                    LabeledContent("Remaining this period", value: "\(account.usage.remaining) of \(account.usage.limit)")
                } else {
                    Text("Sign in to create. Your library and lessons remain available without an account.")
                }
            }
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
            Section("Creative assistant") {
                CreatorTextField(title: "Describe your song idea or ask for a revision", text: $message, lines: 3...6)
                Button("Develop this brief", systemImage: "sparkles") {
                    Task { await creator.askAgent(message) }
                }
                .disabled(creator.busy || creator.account == nil || creator.capabilities?.agent != true || message.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                if creator.capabilities?.agent != true {
                    Text("The assistant is currently unavailable. You can still edit your brief.").font(.caption).foregroundStyle(.secondary)
                }
                if let reply = creator.agentMessage { Text(reply).textSelection(.enabled) }
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
            }.disabled(creator.busy)
            Section("Render") {
                Picker("Song visibility", selection: $visibility) {
                    Text("Private").tag(CreatorVisibility.private)
                    Text("Public · reviewed before sharing").tag(CreatorVisibility.public)
                }
                Toggle("I own or have permission to use the lyrics, music, and any voice likeness in this brief.", isOn: $rights)
                    .fixedSize(horizontal: false, vertical: true)
                Text("Rendering uses your server allowance. The assistant never starts a render for you. Public songs enter moderation.")
                    .font(.caption).foregroundStyle(.secondary)
                Button("Review and render", systemImage: "waveform.badge.plus") { confirmRender = true }
                    .buttonStyle(.borderedProminent)
                    .disabled(!rights || !creator.brief.isRenderable || !creator.canRender || creator.busy)
                    .accessibilityIdentifier("creator.render")
                if !creator.canRender {
                    Text(renderAvailability).font(.caption).foregroundStyle(.secondary)
                }
            }
            Section("Your jobs") {
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
        .formStyle(.grouped)
        .navigationTitle("Create")
        .overlay(alignment: .top) { if creator.busy { ProgressView("Working…").padding(10).background(.regularMaterial, in: Capsule()) } }
        .task(id: creator.identity) { await creator.refreshJobs() }
        .onChange(of: scenePhase) { _, phase in if phase == .active { Task { await creator.refresh() } } }
        .onChange(of: creator.identity) { _, _ in rights = false; message = "" }
        .onChange(of: creator.brief) { _, _ in rights = false }
        .confirmationDialog("Render this song?", isPresented: $confirmRender, titleVisibility: .visible) {
            Button("Render song") { Task { if rights { await creator.render(visibility: visibility) } } }
            Button("Keep editing", role: .cancel) {}
        } message: {
            Text("\(creator.brief.title) · \(creator.brief.duration) seconds · \(visibility.rawValue). This sends the brief to Musia and uses your render allowance.")
        }
        .confirmationDialog("Cancel this queued render?", isPresented: Binding(get: { confirmCancel != nil }, set: { if !$0 { confirmCancel = nil } }), titleVisibility: .visible) {
            Button("Cancel render", role: .destructive) {
                if let job = confirmCancel { Task { await creator.cancel(job) } }; confirmCancel = nil
            }
        }
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
