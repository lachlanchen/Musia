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
        listOf(null, "", "E", "A", "Em7", "Am/G", "F#maj7").forEach { assertNull(curatedShape(it)) }
    }
}
