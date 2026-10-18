import SwiftUI
#if os(macOS)
import AppKit
#endif

// Keep availability decisions at the presentation boundary, not in app state.
struct MusiaNavigation<Content: View>: View {
    @ViewBuilder var content: () -> Content
    var body: some View {
        if #available(macOS 13, *) { NavigationStack { content() } }
        else { NavigationView { content() } }
    }
}

struct MusiaValue: View {
    let title: String
    let value: String
    init(_ title: String, value: String) { self.title = title; self.value = value }
    var body: some View {
        if #available(macOS 13, *) { LabeledContent(title, value: value) }
        else {
            HStack(alignment: .firstTextBaseline) {
                Text(title); Spacer(minLength: 12)
                Text(value).foregroundStyle(.secondary).multilineTextAlignment(.trailing)
            }.accessibilityElement(children: .combine)
        }
    }
}

struct MusiaEmptyView: View {
    let title: String
    let systemImage: String
    var description: Text?
    init(_ title: String, systemImage: String, description: Text? = nil) {
        self.title = title; self.systemImage = systemImage; self.description = description
    }
    var body: some View {
        if #available(macOS 14, *) {
            ContentUnavailableView(title, systemImage: systemImage, description: description)
        } else {
            VStack(spacing: 12) {
                Image(systemName: systemImage).font(.largeTitle).foregroundStyle(.secondary)
                Text(title).font(.title2.bold())
                description?.foregroundStyle(.secondary)
            }.multilineTextAlignment(.center).padding(24).frame(maxWidth: .infinity)
        }
    }
}

struct MusiaIconButton: View {
    let title: String
    let systemImage: String
    let action: () -> Void
    init(_ title: String, systemImage: String, action: @escaping () -> Void) {
        self.title = title; self.systemImage = systemImage; self.action = action
    }
    var body: some View { Button(action: action) { Label(title, systemImage: systemImage) } }
}

struct MusiaFits<Wide: View, Compact: View>: View {
    @ViewBuilder var wide: () -> Wide
    @ViewBuilder var compact: () -> Compact
    var body: some View {
        if #available(macOS 13, *) {
            ViewThatFits(in: .horizontal) { wide(); compact() }
        } else { compact() }
    }
}

struct MusiaMultilineField: View {
    let title: String
    @Binding var text: String
    var lines: ClosedRange<Int> = 1...5
    var body: some View {
        Group {
            if #available(macOS 13, *) {
                TextField(title, text: $text, axis: .vertical).lineLimit(lines)
                    .textFieldStyle(.roundedBorder)
            } else if lines.upperBound == 1 {
                TextField(title, text: $text).textFieldStyle(.roundedBorder)
            } else {
                TextEditor(text: $text).frame(minHeight: CGFloat(max(2, lines.lowerBound)) * 24,
                                            maxHeight: CGFloat(lines.upperBound) * 24)
                    .overlay(RoundedRectangle(cornerRadius: 4).stroke(.secondary.opacity(0.3)))
            }
        }.accessibilityLabel(title)
    }
}

extension View {
    @ViewBuilder func musiaGroupedForm() -> some View {
        if #available(macOS 13, *) { formStyle(.grouped) } else { self.padding() }
    }
}

struct MusiaShareLink: View {
    let url: URL
    var body: some View {
        if #available(macOS 13, *) { ShareLink("Share song", item: url) }
        else {
#if os(macOS)
            MontereyShareButton(url: url).frame(width: 140, height: 28)
#endif
        }
    }
}

// Monterey predates SwiftUI.Layout. Measure tokens, then place whole ruby pairs.
struct MontereyTokenFlow<Token: View>: View {
    let count: Int
    @ViewBuilder var token: (Int) -> Token
    @State private var width: CGFloat = 1
    @State private var sizes: [Int: CGSize] = [:]
    @State private var naturalSizes: [Int: CGSize] = [:]

    private var frames: [CGRect] {
        var x: CGFloat = 0, y: CGFloat = 0, rowHeight: CGFloat = 0
        return (0..<count).map { index in
            let measured = sizes[index] ?? CGSize(width: width, height: 40)
            let size = CGSize(width: min(width, measured.width), height: measured.height)
            if x > 0 && x + size.width > width { x = 0; y += rowHeight + 8; rowHeight = 0 }
            let result = CGRect(x: x, y: y, width: size.width, height: size.height)
            x += size.width + 4; rowHeight = max(rowHeight, size.height)
            return result
        }
    }

    var body: some View {
        let positions = frames
        ZStack(alignment: .topLeading) {
            ForEach(0..<count, id: \.self) { index in
                token(index)
                    .frame(width: min(width, naturalSizes[index]?.width ?? width), alignment: .leading)
                    .fixedSize(horizontal: false, vertical: true)
                    .background(GeometryReader { proxy in
                        Color.clear.preference(key: TokenSizes.self, value: [index: proxy.size])
                    })
                    .offset(x: positions[index].minX, y: positions[index].minY)
            }
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .frame(height: positions.map(\.maxY).max() ?? 0, alignment: .topLeading)
        .background(GeometryReader { proxy in
            Color.clear.preference(key: TokenWidth.self, value: proxy.size.width)
        })
        .background(
            ZStack {
                ForEach(0..<count, id: \.self) { index in
                    token(index).fixedSize().background(GeometryReader { proxy in
                        Color.clear.preference(key: NaturalTokenSizes.self, value: [index: proxy.size])
                    })
                }
            }.hidden().frame(width: 0, height: 0).clipped().accessibilityHidden(true)
        )
        .onPreferenceChange(TokenWidth.self) { width = max(1, $0) }
        .onPreferenceChange(TokenSizes.self) { sizes = $0 }
        .onPreferenceChange(NaturalTokenSizes.self) { naturalSizes = $0 }
    }
}

private struct TokenSizes: PreferenceKey {
    static var defaultValue: [Int: CGSize] = [:]
    static func reduce(value: inout [Int: CGSize], nextValue: () -> [Int: CGSize]) {
        value.merge(nextValue(), uniquingKeysWith: { _, new in new })
    }
}
private struct TokenWidth: PreferenceKey {
    static var defaultValue: CGFloat = 1
    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) { value = nextValue() }
}
private struct NaturalTokenSizes: PreferenceKey {
    static var defaultValue: [Int: CGSize] = [:]
    static func reduce(value: inout [Int: CGSize], nextValue: () -> [Int: CGSize]) {
        value.merge(nextValue(), uniquingKeysWith: { _, new in new })
    }
}

#if os(macOS)
private struct MontereyShareButton: NSViewRepresentable {
    let url: URL
    func makeCoordinator() -> Coordinator { Coordinator(url: url) }
    func makeNSView(context: Context) -> NSButton {
        let button = NSButton(title: "Share song", target: context.coordinator,
                              action: #selector(Coordinator.share(_:)))
        button.bezelStyle = .rounded
        return button
    }
    func updateNSView(_ button: NSButton, context: Context) { context.coordinator.url = url }
    final class Coordinator: NSObject {
        var url: URL
        private var picker: NSSharingServicePicker?
        init(url: URL) { self.url = url }
        @objc func share(_ sender: NSButton) {
            picker = NSSharingServicePicker(items: [url])
            picker?.show(relativeTo: sender.bounds, of: sender, preferredEdge: .minY)
        }
    }
}
#endif
