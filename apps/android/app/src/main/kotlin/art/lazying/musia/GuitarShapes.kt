package art.lazying.musia

data class GuitarShape(val name: String, val frets: List<Int>, val fingers: List<Int>, val description: String)

fun curatedShape(chord: String?): GuitarShape? = when (chord) {
    "Em" -> GuitarShape("Em", listOf(0, 2, 2, 0, 0, 0), listOf(0, 2, 3, 0, 0, 0),
        "Em, standard tuning. From low E on the left to high E on the right: low E open; A second fret, middle finger 2; D second fret, ring finger 3; G open; B open; high E open. All six strings sound.")
    "Am" -> GuitarShape("Am", listOf(-1, 0, 2, 2, 1, 0), listOf(0, 0, 2, 3, 1, 0),
        "Am, standard tuning. From low E on the left to high E on the right: low E muted; A open; D second fret, middle finger 2; G second fret, ring finger 3; B first fret, index finger 1; high E open. Do not sound the low E string.")
    else -> null
}
