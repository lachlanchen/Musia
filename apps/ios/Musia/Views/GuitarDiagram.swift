import MusiaCore
import SwiftUI

struct GuitarDiagram: View {
    let shape: GuitarShape
    var compact = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            if !compact { Text("\(shape.name) fingering").font(.headline) }
            Canvas { context, size in
                let left: CGFloat = 34
                let right = size.width - 24
                let top: CGFloat = 38
                let bottom = size.height - 30
                let stringStep = (right - left) / 5
                let fretStep = (bottom - top) / CGFloat(shape.fretCount)
                for fret in 0...shape.fretCount {
                    var line = Path()
                    let y = top + CGFloat(fret) * fretStep
                    line.move(to: CGPoint(x: left, y: y))
                    line.addLine(to: CGPoint(x: right, y: y))
                    context.stroke(line, with: .color(Palette.ink), lineWidth: fret == 0 && shape.startFret == 1 ? 4 : 1)
                    if fret < shape.fretCount {
                        context.draw(Text(String(shape.startFret + fret)).font(.system(size: 14)),
                                     at: CGPoint(x: 12, y: y + fretStep / 2))
                    }
                }
                for barre in shape.barres {
                    let y = top + (CGFloat(barre.fret - shape.startFret) + 0.5) * fretStep
                    let x = left + CGFloat(barre.firstString) * stringStep
                    let width = CGFloat(barre.lastString - barre.firstString) * stringStep
                    context.fill(Path(roundedRect: CGRect(x: x - 12, y: y - 10, width: width + 24, height: 20), cornerRadius: 10),
                                 with: .color(Palette.teal))
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
                        let y = top + (CGFloat(fret - shape.startFret) + 0.5) * fretStep
                        let dot = Path(ellipseIn: CGRect(x: x - 13, y: y - 13, width: 26, height: 26))
                        context.fill(dot, with: .color(Palette.teal))
                        if let finger = shape.fingers[string] {
                            context.draw(Text(String(finger)).font(.system(size: 16, weight: .bold)).foregroundColor(.white),
                                         at: CGPoint(x: x, y: y))
                        }
                    }
                }
            }
            .aspectRatio(1.15, contentMode: .fit)
#if os(macOS)
            .frame(maxWidth: compact ? 190 : 250)
#else
            .frame(maxWidth: compact ? 190 : 320)
#endif
            .accessibilityHidden(true)
            if !compact {
            Text("Low E to high E - Standard tuning")
                .font(.subheadline).foregroundStyle(.secondary)
            Text("Fingers: 1 index / 2 middle / 3 ring / 4 little")
                .font(.caption).foregroundStyle(.secondary)
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(shape.accessibleText)
        .accessibilityIdentifier("guitar.\(shape.name)")
    }
}
