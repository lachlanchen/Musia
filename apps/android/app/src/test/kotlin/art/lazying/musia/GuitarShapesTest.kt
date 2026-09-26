package art.lazying.musia

import org.junit.Assert.*
import org.junit.Test

class GuitarShapesTest {
    @Test fun emIs022000FromLowEWithMiddleAndRingFingers() {
        val shape = curatedShape("Em")!!
        assertEquals(listOf(0, 2, 2, 0, 0, 0), shape.frets)
        assertEquals(listOf(0, 2, 3, 0, 0, 0), shape.fingers)
        assertTrue(shape.description.contains("low E on the left"))
    }
    @Test fun amIsX02210WithMutedLowEAndOpenHighE() {
        val shape = curatedShape("Am")!!
        assertEquals(listOf(-1, 0, 2, 2, 1, 0), shape.frets)
        assertEquals(listOf(0, 0, 2, 3, 1, 0), shape.fingers)
        assertTrue(shape.description.contains("low E muted"))
    }
    @Test fun otherChordsAreNotInventedOrSimplified() {
        listOf(null, "", "N", "C7", "Em7", "Am/G", "F#maj7").forEach { assertNull(curatedShape(it)) }
    }
    @Test fun allCatalogChordsHaveExactTonesAndVisibleFrets() {
        val roots = listOf("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
        val tuning = listOf(40, 45, 50, 55, 59, 64)
        roots.forEachIndexed { pitch, root ->
            listOf("", "m").forEach { suffix ->
                val shape = curatedShape(root + suffix)!!
                val notes = shape.frets.mapIndexedNotNull { i, fret -> if (fret < 0) null else (tuning[i] + fret) % 12 }
                assertEquals(setOf(pitch, (pitch + if (suffix == "m") 3 else 4) % 12, (pitch + 7) % 12), notes.toSet())
                assertEquals(pitch, notes.first())
                assertTrue(shape.frets.filter { it > 0 }.all { it in shape.startFret until shape.startFret + shape.fretCount })
            }
        }
        assertEquals(6, curatedShape("Eb")!!.startFret)
        assertEquals(2, curatedShape("B")!!.barres.size)
    }
    @Test fun enharmonicAliasesAreSupported() {
        listOf("Db" to "C#", "G\u266dm" to "F#m", "D#:min" to "Ebm", "C:maj" to "C").forEach { (alias, name) ->
            assertEquals(curatedShape(name)!!.frets, curatedShape(alias)!!.frets)
        }
    }
}
