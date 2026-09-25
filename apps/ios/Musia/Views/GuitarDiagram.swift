import MusiaCore
import SwiftUI

struct GuitarDiagram: View {
    let shape: GuitarShape

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("\(shape.name) fingering").font(.headline)
            Canvas { context, size in
                let left: CGFloat = 24
                let right = size.width - 24
                let top: CGFloat = 38
                let bottom = size.height - 30
                let stringStep = (right - left) / 5
                let fretStep = (bottom - top) / 3
                for fret in 0...3 {
                    var line = Path()
                    let y = top + CGFloat(fret) * fretStep
                    line.move(to: CGPoint(x: left, y: y))
                    line.addLine(to: CGPoint(x: right, y: y))
                    context.stroke(line, with: .color(Palette.ink), lineWidth: fret == 0 ? 4 : 1)
                }
                for string in 0..<6 {
                    let x = left + CGFloat(string) * stringStep
                    var line = Path()
                    line.move(to: CGPoint(x: x, y: top))
                    line.addLine(to: CGPoint(x: x, y: bottom))
                    context.stroke(line, with: .color(Palette.ink), lineWidth: string < 3 ? 1.5 : 1)
                    let label = ["E", "A", "D", "G", "B", "e"][string]
                    context.draw(Text(label).font(.system(size: 16, weight: .medium)),
                                 at: CGPoint(x: x, y: bottom + 18))
                    guard let fret = shape.frets[string] else {
                        context.draw(Text("x").font(.system(size: 22, weight: .semibold)).foregroundColor(Palette.coral),
                                     at: CGPoint(x: x, y: 16))
                        continue
                    }
                    if fret == 0 {
                        let circle = Path(ellipseIn: CGRect(x: x - 6, y: 10, width: 12, height: 12))
                        context.stroke(circle, with: .color(Palette.teal), lineWidth: 2)
                    } else {
                        let y = top + (CGFloat(fret) - 0.5) * fretStep
                        let dot = Path(ellipseIn: CGRect(x: x - 13, y: y - 13, width: 26, height: 26))
                        context.fill(dot, with: .color(Palette.teal))
                        if let finger = shape.fingers[string] {
                            context.draw(Text(String(finger)).font(.system(size: 16, weight: .bold)).foregroundColor(.white),
                                         at: CGPoint(x: x, y: y))
                        }
                    }
                }
            }
            .aspectRatio(1.35, contentMode: .fit)
            .frame(maxWidth: 320)
            .accessibilityHidden(true)
            Text("Low E to high E - Standard tuning")
                .font(.subheadline).foregroundStyle(.secondary)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(shape.accessibleText)
        .accessibilityIdentifier("guitar.\(shape.name)")
    }
}
