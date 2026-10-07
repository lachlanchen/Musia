import AppKit
import Foundation

enum IconFailure: Error, CustomStringConvertible {
    case invalid(String)
    var description: String { switch self { case .invalid(let reason): return reason } }
}

func require(_ valid: Bool, _ message: String) throws {
    if !valid { throw IconFailure.invalid(message) }
}

func render(_ image: NSImage, size: Int) throws -> NSBitmapImageRep {
    guard let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: size,
        pixelsHigh: size, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
        isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: size * 4, bitsPerPixel: 32),
        let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
        throw IconFailure.invalid("Cannot render native icon")
    }
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = context
    defer { NSGraphicsContext.restoreGraphicsState() }
    NSColor.clear.setFill()
    NSRect(x: 0, y: 0, width: size, height: size).fill(using: .copy)
    image.draw(in: NSRect(x: 0, y: 0, width: size, height: size),
               from: .zero, operation: .copy, fraction: 1)
    context.flushGraphics()
    return bitmap
}

func inspect(_ bitmap: NSBitmapImageRep) throws -> [String: Any] {
    let size = bitmap.pixelsWide
    func alpha(_ x: Int, _ y: Int) -> CGFloat { bitmap.colorAt(x: x, y: y)?.alphaComponent ?? 0 }
    var left = size, top = size, right = -1, bottom = -1
    var colorful = 0
    for y in 0..<size { for x in 0..<size {
        guard let color = bitmap.colorAt(x: x, y: y)?.usingColorSpace(.deviceRGB),
              color.alphaComponent > 0.8 else { continue }
        left = min(left, x); right = max(right, x)
        top = min(top, y); bottom = max(bottom, y)
        let channels = [color.redComponent, color.greenComponent, color.blueComponent]
        if channels.max()! > 0.4 && channels.max()! - channels.min()! > 0.2 { colorful += 1 }
    }}
    try require(right >= left && bottom >= top, "Empty icon")
    let width = right - left + 1, height = bottom - top + 1
    let extent = Double(width) / Double(size)
    try require((0.8...0.94).contains(extent) && (0.8...0.94).contains(Double(height) / Double(size)),
                "Missing Dock padding or undersized icon: \(extent)")
    try require(abs(width - height) <= max(2, size / 50), "Non-square icon silhouette")
    try require(abs(left - (size - 1 - right)) <= max(2, size / 50)
                && abs(top - (size - 1 - bottom)) <= max(2, size / 50), "Unbalanced icon padding")
    let dx = max(1, width / 20), dy = max(1, height / 20)
    for (x, y) in [(left + dx, top + dy), (right - dx, top + dy),
                   (left + dx, bottom - dy), (right - dx, bottom - dy)] {
        try require(alpha(x, y) < 0.13, "Visible tile has square corners despite transparent canvas")
    }
    let cx = (left + right) / 2, cy = (top + bottom) / 2
    for (x, y) in [(cx, top + dy), (cx, bottom - dy), (left + dx, cy), (right - dx, cy), (cx, cy)] {
        try require(alpha(x, y) > 0.94, "Missing tile center or edge")
    }
    try require(colorful > size * size / 20, "Missing colored ribbon")
    return ["size": size, "bounds": [left, top, right, bottom], "extent": extent,
            "coloredPixels": colorful, "rounded": true]
}

do {
    try require(CommandLine.arguments.count == 3, "Usage: inspect_macos_icon.swift Musia.app output-directory")
    let app = URL(fileURLWithPath: CommandLine.arguments[1]).standardizedFileURL
    let out = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
    let data = try Data(contentsOf: app.appendingPathComponent("Contents/Info.plist"))
    guard let info = try PropertyListSerialization.propertyList(from: data, format: nil) as? [String: Any],
          let name = info["CFBundleIconFile"] as? String else { throw IconFailure.invalid("Missing icon binding") }
    try require(info["CFBundleIdentifier"] as? String == "art.lazying.musia", "Not Musia")
    try require(name == "AppIcon" || name == "AppIcon.icns", "Unexpected icon file")
    let icns = app.appendingPathComponent("Contents/Resources/AppIcon.icns")
    guard let compiled = NSImage(contentsOf: icns) else { throw IconFailure.invalid("Cannot decode compiled ICNS") }
    let native = NSWorkspace.shared.icon(forFile: app.path)
    try FileManager.default.createDirectory(at: out, withIntermediateDirectories: true)
    var results: [[String: Any]] = []
    for (source, image) in [("compiled-icns", compiled), ("workspace", native)] {
        for size in [64, 512] {
            let bitmap = try render(image, size: size)
            let filename = "\(source)-\(size).png"
            guard let png = bitmap.representation(using: .png, properties: [:]) else {
                throw IconFailure.invalid("Cannot save inspection evidence")
            }
            try png.write(to: out.appendingPathComponent(filename))
            var result = try inspect(bitmap)
            result["source"] = source; result["file"] = filename
            results.append(result)
        }
    }
    let report: [String: Any] = ["state": "passed", "bundle": "art.lazying.musia",
        "version": info["CFBundleShortVersionString"] ?? "", "build": info["CFBundleVersion"] ?? "",
        "app": app.path, "checks": results]
    let json = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
    print(String(decoding: json, as: UTF8.self))
} catch {
    FileHandle.standardError.write(Data("Icon inspection failed: \(error)\n".utf8))
    exit(1)
}
