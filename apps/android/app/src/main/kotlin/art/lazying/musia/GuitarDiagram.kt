package art.lazying.musia

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.unit.dp

@Composable fun GuitarDiagram(chord: String?, upcoming: Boolean = false) {
    val shape = curatedShape(chord)
    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(if (upcoming) "Next shape: ${chord ?: "--"}" else "Chord shape: ${chord ?: "--"}", style = MaterialTheme.typography.titleLarge)
        if (shape == null) {
            Text(if (chord.isNullOrBlank()) "Waiting for the next chord" else "Diagram not available for $chord yet", color = MaterialTheme.colorScheme.onSurfaceVariant)
            return@Column
        }
        Text("Standard tuning / Low E to high e", style = MaterialTheme.typography.bodySmall)
        val lineColor = MaterialTheme.colorScheme.outline
        val barreColor = MaterialTheme.colorScheme.primary
        Column(Modifier.widthIn(max = 420.dp).fillMaxWidth().clearAndSetSemantics { contentDescription = shape.description }) {
            Row(Modifier.fillMaxWidth().padding(start = 24.dp)) {
                listOf("E", "A", "D", "G", "B", "e").forEach { name ->
                    Box(Modifier.weight(1f).heightIn(min = 32.dp), contentAlignment = Alignment.Center) { Text(name) }
                }
            }
            Row(Modifier.fillMaxWidth().padding(start = 24.dp)) {
                shape.frets.forEach { fret ->
                    Box(Modifier.weight(1f).heightIn(min = 32.dp), contentAlignment = Alignment.Center) { Text(if (fret == -1) "X" else if (fret == 0) "O" else "") }
                }
            }
            Row(Modifier.fillMaxWidth()) {
                Column(Modifier.width(24.dp)) {
                    (shape.startFret until shape.startFret + shape.fretCount).forEach { fret -> Box(Modifier.height(56.dp), contentAlignment = Alignment.Center) { Text(fret.toString(), style = MaterialTheme.typography.bodySmall) } }
                }
                Box(Modifier.weight(1f).height((56 * shape.fretCount).dp)) {
                    Canvas(Modifier.matchParentSize()) {
                        val left = size.width / 12f
                        val right = size.width - left
                        for (string in 0..5) {
                            val x = size.width * (string + .5f) / 6
                            drawLine(lineColor, Offset(x, 0f), Offset(x, size.height), (2.2f - string * .2f).dp.toPx())
                        }
                        for (fret in 0..shape.fretCount) {
                            val y = size.height * fret / shape.fretCount
                            drawLine(lineColor, Offset(left, y), Offset(right, y), if (fret == 0 && shape.startFret == 1) 4.dp.toPx() else 1.dp.toPx())
                        }
                        for (barre in shape.barres) {
                            val x = size.width * (barre.firstString + .5f) / 6
                            val end = size.width * (barre.lastString + .5f) / 6
                            val y = size.height * (barre.fret - shape.startFret + .5f) / shape.fretCount
                            val radius = 12.dp.toPx()
                            drawRoundRect(barreColor, Offset(x - radius, y - radius), Size(end - x + 2 * radius, 2 * radius), CornerRadius(radius))
                        }
                    }
                    Column {
                        for (fret in shape.startFret until shape.startFret + shape.fretCount) Row(Modifier.fillMaxWidth().height(56.dp)) {
                            for (string in 0..5) Box(Modifier.weight(1f).fillMaxHeight(), contentAlignment = Alignment.Center) {
                                if (shape.frets[string] == fret) Box(Modifier.size(36.dp).background(MaterialTheme.colorScheme.primary, CircleShape), contentAlignment = Alignment.Center) {
                                    Text(shape.fingers[string].toString(), color = MaterialTheme.colorScheme.onPrimary, style = MaterialTheme.typography.labelLarge)
                                }
                            }
                        }
                    }
                }
            }
        }
        Text("O open / X muted", style = MaterialTheme.typography.bodySmall)
        Text("Fingers: 1 index / 2 middle / 3 ring / 4 little", style = MaterialTheme.typography.bodySmall)
    }
}
