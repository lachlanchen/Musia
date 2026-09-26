package art.lazying.musia

data class GuitarBarre(val fret: Int, val firstString: Int, val lastString: Int, val finger: Int)
data class GuitarShape(val name: String, val frets: List<Int>, val fingers: List<Int>, val barres: List<GuitarBarre>) {
    val startFret: Int get() = if (frets.max() <= 4) 1 else frets.filter { it > 0 }.min()
    val fretCount: Int get() = 4
    val description: String get() {
        val strings = listOf("low E", "A", "D", "G", "B", "high E")
        val notes = strings.indices.joinToString("; ") { i ->
            when (frets[i]) {
                -1 -> "${strings[i]} muted"
                0 -> "${strings[i]} open"
                else -> "${strings[i]} fret ${frets[i]}, finger ${fingers[i]}"
            }
        }
        val bars = barres.joinToString(" ") { "Barre fret ${it.fret}, finger ${it.finger}, ${strings[it.firstString]} to ${strings[it.lastString]}." }
        return "$name, standard tuning. From low E on the left to high E on the right: $notes. $bars"
    }
}

fun curatedShape(chord: String?): GuitarShape? {
    val label = chord?.trim()?.replace("\u266f", "#")?.replace("\u266d", "b")
        ?.replace(":maj", "")?.replace(":min", "m") ?: return null
    val minor = label.endsWith("m")
    val root = if (minor) label.dropLast(1) else label
    val aliases = mapOf("Db" to "C#", "D#" to "Eb", "Gb" to "F#", "G#" to "Ab", "A#" to "Bb", "Cb" to "B", "B#" to "C", "E#" to "F", "Fb" to "E")
    val row = shapes[(aliases[root] ?: root) + if (minor) "m" else ""] ?: return null
    return GuitarShape(label, row[0], row[1], row.drop(2).map { GuitarBarre(it[0], it[1], it[2], it[3]) })
}

// BEGIN GENERATED SHAPES
private val shapes: Map<String, List<List<Int>>> = mapOf(
    "A" to listOf(listOf(-1, 0, 2, 2, 2, 0), listOf(0, 0, 1, 2, 3, 0)),
    "Am" to listOf(listOf(-1, 0, 2, 2, 1, 0), listOf(0, 0, 2, 3, 1, 0)),
    "Bb" to listOf(listOf(-1, 1, 3, 3, 3, 1), listOf(0, 1, 3, 3, 3, 1), listOf(1, 1, 5, 1), listOf(3, 2, 4, 3)),
    "Bbm" to listOf(listOf(-1, 1, 3, 3, 2, 1), listOf(0, 1, 3, 4, 2, 1), listOf(1, 1, 5, 1)),
    "B" to listOf(listOf(-1, 2, 4, 4, 4, 2), listOf(0, 1, 3, 3, 3, 1), listOf(2, 1, 5, 1), listOf(4, 2, 4, 3)),
    "Bm" to listOf(listOf(-1, 2, 4, 4, 3, 2), listOf(0, 1, 3, 4, 2, 1), listOf(2, 1, 5, 1)),
    "C" to listOf(listOf(-1, 3, 2, 0, 1, 0), listOf(0, 3, 2, 0, 1, 0)),
    "Cm" to listOf(listOf(-1, 3, 5, 5, 4, 3), listOf(0, 1, 3, 4, 2, 1), listOf(3, 1, 5, 1)),
    "C#" to listOf(listOf(-1, 4, 6, 6, 6, 4), listOf(0, 1, 3, 3, 3, 1), listOf(4, 1, 5, 1), listOf(6, 2, 4, 3)),
    "C#m" to listOf(listOf(-1, 4, 6, 6, 5, 4), listOf(0, 1, 3, 4, 2, 1), listOf(4, 1, 5, 1)),
    "D" to listOf(listOf(-1, -1, 0, 2, 3, 2), listOf(0, 0, 0, 1, 3, 2)),
    "Dm" to listOf(listOf(-1, -1, 0, 2, 3, 1), listOf(0, 0, 0, 2, 3, 1)),
    "Eb" to listOf(listOf(-1, 6, 8, 8, 8, 6), listOf(0, 1, 3, 3, 3, 1), listOf(6, 1, 5, 1), listOf(8, 2, 4, 3)),
    "Ebm" to listOf(listOf(-1, 6, 8, 8, 7, 6), listOf(0, 1, 3, 4, 2, 1), listOf(6, 1, 5, 1)),
    "E" to listOf(listOf(0, 2, 2, 1, 0, 0), listOf(0, 2, 3, 1, 0, 0)),
    "Em" to listOf(listOf(0, 2, 2, 0, 0, 0), listOf(0, 2, 3, 0, 0, 0)),
    "F" to listOf(listOf(1, 3, 3, 2, 1, 1), listOf(1, 3, 4, 2, 1, 1), listOf(1, 0, 5, 1)),
    "Fm" to listOf(listOf(1, 3, 3, 1, 1, 1), listOf(1, 3, 4, 1, 1, 1), listOf(1, 0, 5, 1)),
    "F#" to listOf(listOf(2, 4, 4, 3, 2, 2), listOf(1, 3, 4, 2, 1, 1), listOf(2, 0, 5, 1)),
    "F#m" to listOf(listOf(2, 4, 4, 2, 2, 2), listOf(1, 3, 4, 1, 1, 1), listOf(2, 0, 5, 1)),
    "G" to listOf(listOf(3, 2, 0, 0, 0, 3), listOf(3, 2, 0, 0, 0, 4)),
    "Gm" to listOf(listOf(3, 5, 5, 3, 3, 3), listOf(1, 3, 4, 1, 1, 1), listOf(3, 0, 5, 1)),
    "Ab" to listOf(listOf(4, 6, 6, 5, 4, 4), listOf(1, 3, 4, 2, 1, 1), listOf(4, 0, 5, 1)),
    "Abm" to listOf(listOf(4, 6, 6, 4, 4, 4), listOf(1, 3, 4, 1, 1, 1), listOf(4, 0, 5, 1)),
)
// END GENERATED SHAPES
