import MusiaCore
import SwiftUI

// Keep each annotation with its base text, wrapping at token boundaries.
private struct RubyFlowLayout: Layout {
    var spacing: CGFloat
    var rowSpacing: CGFloat

    private func arrange(width: CGFloat, subviews: Subviews) -> (CGSize, [CGRect]) {
        var x: CGFloat = 0, y: CGFloat = 0, rowHeight: CGFloat = 0
        var frames: [CGRect] = []
        for view in subviews {
            let size = view.sizeThatFits(ProposedViewSize(width: width, height: nil))
            if x > 0 && x + size.width > width {
                x = 0; y += rowHeight + rowSpacing; rowHeight = 0
            }
            frames.append(CGRect(origin: CGPoint(x: x, y: y), size: size))
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
        return (CGSize(width: width, height: y + rowHeight), frames)
    }

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        arrange(width: proposal.width ?? 320, subviews: subviews).0
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let frames = arrange(width: bounds.width, subviews: subviews).1
        for (view, frame) in zip(subviews, frames) {
            view.place(at: CGPoint(x: bounds.minX + frame.minX, y: bounds.minY + frame.minY),
                       proposal: ProposedViewSize(frame.size))
        }
    }
}

struct PracticeView: View {
    @EnvironmentObject private var player: PlaybackController
    @Environment(\.dismiss) private var dismiss
    @Environment(\.dynamicTypeSize) private var dynamicType
    @State private var scrubbing = false
    @State private var scrubPosition = 0.0
    @State private var stage = true
    @AppStorage("lyricLanguages") private var lyricLanguages = LyricLanguages.defaults

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: stage ? 16 : 24) {
                if player.loading { ProgressView("Loading song...").frame(maxWidth: .infinity).padding() }
                if let issue = player.issue { ErrorNotice(message: issue) { player.retry() } }
                if let song = player.song, let asset = player.asset {
                    Picker("Player view", selection: $stage) {
                        Label("Stage", systemImage: "play.rectangle").tag(true)
                        Label("Practice", systemImage: "guitars").tag(false)
                    }
                    .pickerStyle(.segmented)
                    .accessibilityIdentifier("player.view")
                    if stage {
                        ViewThatFits(in: .horizontal) {
                            HStack(alignment: .top, spacing: 28) {
                                stageHeader(song, asset: asset).frame(width: 300)
                                lyrics(asset, showUpcoming: false).frame(minWidth: 340)
                            }.frame(minWidth: 720)
                            VStack(alignment: .leading, spacing: 16) {
                                stageHeader(song, asset: asset)
                                lyrics(asset, showUpcoming: false)
                            }
                        }
                        Divider()
                        stageGuitar(asset)
                        DisclosureGroup("Playback settings") {
                            VStack(alignment: .leading, spacing: 16) {
                                assetPicker(song, asset: asset)
                                speedControl
                                loopControls(asset)
                                analysis(asset)
                            }.padding(.top, 12)
                        }
                    } else {
#if os(macOS)
                    HStack(alignment: .top, spacing: 32) {
                        VStack(alignment: .leading, spacing: 24) {
                            heading(song)
                            assetPicker(song, asset: asset)
                            transport
                            Divider()
                            loopControls(asset)
                        }
                        .frame(width: 300)
                        Divider()
                        VStack(alignment: .leading, spacing: 24) {
                            modePicker
                            Text(PracticeGuidance.text(songID: song.id, mode: player.mode))
                                .foregroundStyle(.secondary)
                            pulse(song: song, asset: asset)
                            lyrics(asset)
                            if player.mode == .tap { tapPad(asset) }
                            if player.mode == .play || !asset.chords.isEmpty { harmony(asset) }
                            Divider()
                            analysis(asset)
                        }
                        .frame(maxWidth: .infinity, alignment: .topLeading)
                    }
#else
                    heading(song)
                    assetPicker(song, asset: asset)
                    modePicker
                    Text(PracticeGuidance.text(songID: song.id, mode: player.mode))
                        .font(.body).foregroundStyle(.secondary)
                    transport
                    Divider()
                    pulse(song: song, asset: asset)
                    lyrics(asset)
                    if player.mode == .tap { tapPad(asset) }
                    if player.mode == .play || !asset.chords.isEmpty { harmony(asset) }
                    Divider()
                    loopControls(asset)
                    analysis(asset)
#endif
                    }
                }
            }
#if os(macOS)
            .frame(maxWidth: stage ? 840 : 1240)
#else
            .frame(maxWidth: 760)
#endif
            .padding(20)
            .frame(maxWidth: .infinity)
        }
        .background(Color.white)
        .navigationTitle(stage ? "Now playing" : "Practice")
        .safeAreaInset(edge: .bottom, spacing: 0) {
            if stage && player.asset != nil {
                stageTransport.padding(.horizontal, 20).padding(.vertical, 8)
                    .frame(maxWidth: .infinity).background(Palette.surface)
                    .overlay(alignment: .top) { Divider() }
            }
        }
#if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button { dismiss() } label: { Image(systemName: "chevron.down") }
                    .accessibilityLabel("Close practice").help("Close practice")
                    .accessibilityIdentifier("practice.close")
            }
        }
#endif
        .onChange(of: player.asset?.id) { _, _ in scrubbing = false }
        .onChange(of: player.song?.id, initial: true) { _, _ in stage = !player.isLocalExercise }
    }

    private func stageHeader(_ song: Song, asset: SongAsset) -> some View {
        let hasBeats = asset.confidence.beats != .unavailable && !asset.beats.isEmpty
        let strength = player.isPlaying && !player.seeking && hasBeats
            ? Timeline.pulse(in: asset.beats, at: player.position, rate: player.rate) : 0
        return HStack(alignment: .top, spacing: 16) {
            CoverView(url: song.coverUrl, local: player.isLocalExercise, size: dynamicType.isAccessibilitySize ? 64 : 96)
            VStack(alignment: .leading, spacing: 10) {
                Text(song.title).font(.title3.bold()).fixedSize(horizontal: false, vertical: true)
                Text(song.artist).font(.subheadline).foregroundStyle(.secondary)
                ViewThatFits(in: .horizontal) {
                    HStack(spacing: 16) { stageMetrics(asset, hasBeats: hasBeats, strength: strength) }
                    VStack(alignment: .leading, spacing: 8) { stageMetrics(asset, hasBeats: hasBeats, strength: strength) }
                }
            }.frame(maxWidth: .infinity, alignment: .leading)
        }
        .accessibilityIdentifier("stage.header")
    }

    @ViewBuilder private func stageMetrics(_ asset: SongAsset, hasBeats: Bool, strength: Double) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack(spacing: 5) {
                Image(systemName: "metronome.fill").foregroundStyle(strength > 0.2 ? Palette.coral : Palette.teal)
                Text(hasBeats && asset.bpm != nil ? String(format: "%.0f BPM", (asset.bpm ?? 0) * player.rate) : "BPM unavailable")
                    .font(.headline).monospacedDigit()
            }
            Text(hasBeats ? asset.confidence.beats.label : "No beat reference").font(.caption).foregroundStyle(.secondary)
        }
        VStack(alignment: .leading, spacing: 2) {
            Text(String(format: "%.2gx", player.rate)).font(.headline).monospacedDigit()
            Text(asset.timeSignature ?? "Original pitch").font(.caption).foregroundStyle(.secondary)
        }
    }

    private var stageTransport: some View {
        VStack(spacing: 0) {
            Slider(value: Binding(
                get: { scrubbing ? scrubPosition : min(player.position, max(0.01, player.duration)) },
                set: { scrubPosition = $0 }
            ), in: 0...max(0.01, player.duration), onEditingChanged: { editing in
                if editing { scrubPosition = player.position }
                scrubbing = editing
                if !editing { player.seek(to: scrubPosition) }
            }).disabled(!player.ready).accessibilityLabel("Playback position")
            HStack(spacing: 12) {
                Text(Timeline.timestamp(scrubbing ? scrubPosition : player.position)).font(.caption.monospacedDigit())
                Spacer(minLength: 0)
                TransportButton(title: "Back 10 seconds", symbol: "gobackward.10") { player.seek(to: player.position - 10) }
                TransportButton(title: player.isPlaying || player.waiting ? "Pause" : "Play",
                                symbol: player.isPlaying || player.waiting ? "pause.fill" : "play.fill") { player.togglePlayback() }
                    .accessibilityIdentifier("practice.transport.play")
                TransportButton(title: "Forward 10 seconds", symbol: "goforward.10") { player.seek(to: player.position + 10) }
                Spacer(minLength: 0)
                Text(Timeline.timestamp(player.duration)).font(.caption.monospacedDigit())
            }.disabled(!player.ready)
            if player.waiting { ProgressView().accessibilityLabel("Buffering audio") }
        }.frame(maxWidth: 760)
    }

    private func stageGuitar(_ asset: SongAsset) -> some View {
        let available = asset.confidence.chords != .unavailable && !asset.chords.isEmpty
        let current = available ? Timeline.current(in: asset.chords, at: player.position) : nil
        let next = available ? Timeline.next(in: asset.chords, at: player.position) : nil
        return VStack(alignment: .leading, spacing: 12) {
            HStack {
                Label("Guitar", systemImage: "guitars").font(.headline)
                Spacer()
                Text(available ? asset.confidence.chords.label : "Unavailable").font(.caption).foregroundStyle(.secondary)
            }
            HStack(alignment: .top, spacing: 24) {
                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 8) {
                        Text("Now").font(.caption).foregroundStyle(.secondary)
                        Text(current?.name ?? "--").font(.title.bold()).foregroundStyle(Palette.teal)
                    }
                    if let name = current?.name, let shape = GuitarShape.known(name) {
                        GuitarDiagram(shape: shape, compact: true)
                    } else {
                        Label(current == nil ? "No chord at this position" : "Fingering unavailable", systemImage: "guitars")
                            .font(.subheadline).foregroundStyle(.secondary)
                    }
                }.frame(maxWidth: .infinity, minHeight: 200, alignment: .topLeading)
                VStack(alignment: .leading, spacing: 6) {
                    Text("Next").font(.caption).foregroundStyle(.secondary)
                    Text(next?.name ?? "--").font(.title2.bold())
                    if let next { Text(Timeline.timestamp(next.start)).font(.caption.monospacedDigit()).foregroundStyle(.secondary) }
                    Text("E A D G B e").font(.caption).foregroundStyle(.secondary)
                }.frame(minWidth: 80, alignment: .leading)
            }
        }.accessibilityIdentifier("stage.guitar")
    }

    private func heading(_ song: Song) -> some View {
        HStack(alignment: .top, spacing: 16) {
            CoverView(url: song.coverUrl, local: player.isLocalExercise, size: 88)
            VStack(alignment: .leading, spacing: 6) {
                Text(song.title).font(.title2.bold()).foregroundStyle(Palette.ink)
                    .fixedSize(horizontal: false, vertical: true)
                Text(song.artist).font(.body).foregroundStyle(.secondary)
                if song.id == FirstPulse.id {
                    Text("Synthesized exercise").font(.subheadline).foregroundStyle(Palette.coral)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    @ViewBuilder private func assetPicker(_ song: Song, asset: SongAsset) -> some View {
        if song.assets.count > 1 {
            Picker("Audio version", selection: Binding(get: { asset.id }, set: { player.selectAsset($0) })) {
                ForEach(song.assets) { version in Text("\(version.label) (\(version.language))").tag(version.id) }
            }
            .pickerStyle(.menu)
        } else {
            Text(asset.label).font(.subheadline).foregroundStyle(.secondary)
        }
    }

    private var modePicker: some View {
        Group {
            if dynamicType.isAccessibilitySize { modes.pickerStyle(.menu) }
            else { modes.pickerStyle(.segmented) }
        }
    }

    private var modes: some View {
        Picker("Practice mode", selection: Binding(get: { player.mode }, set: { player.setMode($0) })) {
            ForEach(PracticeMode.allCases, id: \.self) { Text($0.rawValue).tag($0) }
        }
        .accessibilityIdentifier("practice.mode")
    }

    private var transport: some View {
        VStack(spacing: 16) {
            Slider(value: Binding(
                get: { scrubbing ? scrubPosition : min(player.position, max(0.01, player.duration)) },
                set: { scrubPosition = $0 }
            ), in: 0...max(0.01, player.duration), onEditingChanged: { editing in
                if editing { scrubPosition = player.position }
                scrubbing = editing
                if !editing { player.seek(to: scrubPosition) }
            })
            .disabled(!player.ready)
            .accessibilityLabel("Playback position")
            .accessibilityValue(Timeline.timestamp(player.position))
            HStack {
                Text(Timeline.timestamp(scrubbing ? scrubPosition : player.position))
                Spacer()
                if player.waiting { ProgressView().accessibilityLabel("Buffering audio") }
                Text(Timeline.timestamp(player.duration))
            }
            .font(.subheadline.monospacedDigit()).foregroundStyle(.secondary)
            HStack(spacing: 28) {
                TransportButton(title: "Back 10 seconds", symbol: "gobackward.10") { player.seek(to: player.position - 10) }
                TransportButton(title: player.isPlaying || player.waiting ? "Pause" : "Play",
                                symbol: player.isPlaying || player.waiting ? "pause.fill" : "play.fill", primary: true) {
                    player.togglePlayback()
                }
                .accessibilityIdentifier("practice.transport.play")
                TransportButton(title: "Forward 10 seconds", symbol: "goforward.10") { player.seek(to: player.position + 10) }
            }
            .disabled(!player.ready)
            speedControl
        }
    }

    private var speedControl: some View {
            VStack(alignment: .leading, spacing: 4) {
                LabeledContent("Speed", value: String(format: "%.2gx", player.rate))
                    .font(.headline).monospacedDigit()
                Slider(value: Binding(get: { player.rate }, set: { player.setRate($0) }), in: 0.25...2, step: 0.05)
                    .accessibilityLabel("Pitch-preserving playback speed")
                    .accessibilityValue(String(format: "%.2g times", player.rate))
                HStack {
                    Text("0.25x")
                    Spacer()
                    Text("Pitch preserved")
                    Spacer()
                    Text("2x")
                }
                .font(.subheadline).foregroundStyle(.secondary)
            }
    }

    private func pulse(song: Song, asset: SongAsset) -> some View {
        let hasBeats = asset.confidence.beats != .unavailable && !asset.beats.isEmpty
        let strength = player.isPlaying && !player.seeking && hasBeats
            ? Timeline.pulse(in: asset.beats, at: player.position, rate: player.rate) : 0
        return HStack(spacing: 16) {
            Image(systemName: "metronome.fill")
                .font(.largeTitle)
                .foregroundStyle(strength > 0.2 ? Palette.coral : Palette.teal)
                .frame(width: 64, height: 64)
                .background(Palette.mint, in: RoundedRectangle(cornerRadius: 8))
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(Palette.coral.opacity(strength), lineWidth: 4))
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 4) {
                if let bpm = asset.bpm, hasBeats {
                    Text("\(bpm * player.rate, specifier: "%.0f") BPM").font(.title3.bold()).monospacedDigit()
                } else { Text("Pulse").font(.headline) }
                Text(PracticeGuidance.phase(songID: song.id, time: player.position,
                                           playing: player.isPlaying, hasBeats: hasBeats))
                    .font(.subheadline).foregroundStyle(.secondary)
                ConfidenceLabel(name: "Beats", value: hasBeats ? asset.confidence.beats : .unavailable)
            }
        }
    }

    private func lyrics(_ asset: SongAsset, showUpcoming: Bool = true) -> some View {
        let tracks = asset.displayLyricTracks
        let selected = tracks.filter { LyricLanguages.selected($0.language, in: lyricLanguages) }
        return VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Lyrics").font(.headline)
                Spacer()
                if !tracks.isEmpty {
                    Menu {
                        ForEach(tracks) { track in
                            Toggle(LyricLanguages.label(track.language), isOn: Binding(
                                get: { LyricLanguages.selected(track.language, in: lyricLanguages) },
                                set: { lyricLanguages = LyricLanguages.setting(track.language, enabled: $0, in: lyricLanguages) }
                            ))
                        }
                    } label: { Label("Languages", systemImage: "character.bubble") }
                    .accessibilityIdentifier("practice.lyricLanguages")
                }
            }
            if tracks.isEmpty {
                Label("No timed lyrics", systemImage: "music.note").foregroundStyle(.secondary)
            } else if selected.isEmpty {
                Text("Lyrics hidden").foregroundStyle(.secondary)
            } else {
                if selected.allSatisfy({ Timeline.current(in: $0.lines, at: player.position) == nil }) {
                    Label("Instrumental / lyric gap", systemImage: "music.note").foregroundStyle(.secondary)
                }
                ForEach(selected) { track in
                    let line = Timeline.current(in: track.lines, at: player.position)
                    let next = Timeline.next(in: track.lines, at: player.position)
                    if showUpcoming || line != nil {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(LyricLanguages.label(track.language)).font(.caption.weight(.semibold)).foregroundStyle(.secondary)
                        if let line { lyricLine(line, upcoming: false, compact: !showUpcoming) }
                        if showUpcoming, let next { lyricLine(next, upcoming: true) }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .accessibilityIdentifier("practice.lyrics.\(track.language)")
                    }
                }
            }
        }
        .frame(maxWidth: .infinity, minHeight: showUpcoming ? 60 : 200, alignment: .topLeading)
    }

    @ViewBuilder private func lyricLine(_ line: LyricLine, upcoming: Bool, compact: Bool = false) -> some View {
        let rendering = LyricRendering(line: line)
        let hasRuby = rendering.parts.contains { !($0.reading ?? "").isEmpty }
        let font: Font = upcoming ? .body : (compact ? .title3.weight(.semibold) : .title2.weight(.semibold))
        Group {
            if hasRuby {
                RubyFlowLayout(spacing: 4, rowSpacing: 8) {
                    ForEach(Array(rendering.parts.enumerated()), id: \.offset) { _, part in
                        VStack(spacing: 2) {
                            Text(part.reading ?? " ").font(.caption).foregroundStyle(.secondary)
                            Text(part.text).font(font)
                                .foregroundStyle(!upcoming && part.isActive(at: player.position) ? Palette.teal : Palette.ink)
                        }
                        .fixedSize(horizontal: false, vertical: true)
                    }
                }
            } else {
                Text(highlighted(rendering, upcoming: upcoming)).font(font)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .opacity(upcoming ? 0.65 : 1)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel((upcoming ? "Next: " : "") + line.text)
    }

    private func highlighted(_ rendering: LyricRendering, upcoming: Bool) -> AttributedString {
        var text = AttributedString()
        for part in rendering.parts {
            var piece = AttributedString(part.text)
            piece.foregroundColor = !upcoming && part.isActive(at: player.position) ? Palette.teal : Palette.ink
            text.append(piece)
        }
        return text
    }

    private func tapPad(_ asset: SongAsset) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Button { player.tap() } label: {
                Label("Tap", systemImage: "hand.tap.fill")
                    .font(.title2.bold())
                    .frame(maxWidth: .infinity, minHeight: 100)
                    .foregroundStyle(.white)
                    .background(player.canTap ? Palette.coral : Color.gray, in: RoundedRectangle(cornerRadius: 8))
            }
            .buttonStyle(.plain)
            .disabled(!player.canTap)
            .accessibilityIdentifier("practice.tap")
            Text(player.canTap ? player.tapMessage : (player.isPlaying ? "Outside the beat reference" : "Start playback to tap"))
                .font(.headline).frame(minHeight: 28, alignment: .leading)
            Text("Screen-tap timing only. Not guitar or singing grading. Device and Bluetooth latency are not calibrated.")
                .font(.subheadline).foregroundStyle(.secondary)
        }
    }

    private func harmony(_ asset: SongAsset) -> some View {
        let available = asset.confidence.chords != .unavailable
        let current = available ? Timeline.current(in: asset.chords, at: player.position) : nil
        let next = available ? Timeline.next(in: asset.chords, at: player.position) : nil
        return VStack(alignment: .leading, spacing: 12) {
            if dynamicType.isAccessibilitySize {
                chordColumn("Current chord", name: current?.name)
                chordColumn("Next chord", name: next?.name)
            } else {
                HStack(alignment: .top, spacing: 20) {
                    chordColumn("Current chord", name: current?.name)
                    chordColumn("Next chord", name: next?.name)
                }
            }
            ConfidenceLabel(name: "Chords", value: asset.chords.isEmpty ? .unavailable : asset.confidence.chords)
            if player.mode == .play {
                if let name = current?.name, let shape = GuitarShape.known(name) {
                    GuitarDiagram(shape: shape)
                } else if player.song?.id == FirstPulse.id && player.position < 4,
                          let shape = GuitarShape.known("Em") {
                    GuitarDiagram(shape: shape)
                } else if let name = current?.name {
                    Text("No fingering diagram for \(name)").font(.subheadline).foregroundStyle(.secondary)
                }
                Text("Play along - no microphone or performance grading.")
                    .font(.subheadline).foregroundStyle(.secondary)
                if asset.confidence.melody != .unavailable,
                   let note = Timeline.current(in: asset.melody, at: player.position) {
                    LabeledContent("Reference note", value: "\(note.note.text)  (\(note.numberNote.text))")
                    ConfidenceLabel(name: "Melody", value: asset.confidence.melody)
                }
            }
        }
    }

    private func chordColumn(_ label: String, name: String?) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label).font(.subheadline).foregroundStyle(.secondary)
            Text(name ?? "None").font(.title.weight(.semibold))
                .foregroundStyle(name == nil ? .secondary : Palette.teal)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func loopControls(_ asset: SongAsset) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Label("Phrase loop", systemImage: "repeat").font(.headline)
                Spacer()
                if player.loop != nil || player.markerA != nil {
                    Button { player.clearLoop() } label: { Image(systemName: "xmark.circle") }
                        .frame(minWidth: 44, minHeight: 44)
                        .accessibilityLabel("Clear loop").help("Clear loop")
                }
            }
            if let loop = player.loop {
                Text("A \(Timeline.timestamp(loop.start))  -  B \(Timeline.timestamp(loop.end))")
                    .font(.body.monospacedDigit()).foregroundStyle(Palette.teal)
            } else if let marker = player.markerA {
                Text("A \(Timeline.timestamp(marker))").font(.body.monospacedDigit())
            }
            HStack(spacing: 16) {
                Button { player.markA() } label: { Label("Set A", systemImage: "a.circle") }
                    .disabled(!player.ready)
                Button { player.markB() } label: { Label("Set B", systemImage: "b.circle") }
                    .disabled(!player.ready || player.markerA.map { player.position - $0 < 0.1 } != false)
            }
            .buttonStyle(.bordered)
            ForEach(asset.loopPhrases) { phrase in
                Button { player.setLoop(start: phrase.start, end: phrase.end) } label: {
                    HStack(alignment: .top, spacing: 12) {
                        Image(systemName: player.loop?.start == phrase.start && player.loop?.end == phrase.end
                              ? "repeat.circle.fill" : "repeat.circle")
                            .font(.title2)
                        VStack(alignment: .leading, spacing: 4) {
                            Text(phrase.text).font(.body)
                            Text("\(Timeline.timestamp(phrase.start)) - \(Timeline.timestamp(phrase.end))")
                                .font(.subheadline.monospacedDigit()).foregroundStyle(.secondary)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .padding(.vertical, 6)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain).foregroundStyle(Palette.teal)
                .disabled(!player.ready || phrase.end > player.duration)
                .accessibilityLabel("Loop \(phrase.text), \(Timeline.timestamp(phrase.start)) to \(Timeline.timestamp(phrase.end))")
            }
        }
    }

    private func analysis(_ asset: SongAsset) -> some View {
        DisclosureGroup("Reference details") {
            VStack(alignment: .leading, spacing: 12) {
                ConfidenceLabel(name: "Beats", value: asset.beats.isEmpty ? .unavailable : asset.confidence.beats)
                ConfidenceLabel(name: "Chords", value: asset.chords.isEmpty ? .unavailable : asset.confidence.chords)
                ConfidenceLabel(name: "Melody", value: asset.melody.isEmpty ? .unavailable : asset.confidence.melody)
                if let signature = asset.timeSignature { LabeledContent("Time signature", value: signature) }
                Text("Verified describes the reference data, not your performance. Analyzed and estimated events may be wrong. Missing events are not inferred.")
                    .font(.subheadline).foregroundStyle(.secondary)
            }
            .padding(.top, 12)
        }
    }
}
