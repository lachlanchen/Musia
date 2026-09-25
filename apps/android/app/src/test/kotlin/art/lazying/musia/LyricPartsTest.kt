package art.lazying.musia

import org.junit.Assert.*
import org.junit.Test

class LyricPartsTest {
    private fun line(text: String, vararg tokens: String): Lyric = Lyric("line", 0.0, 20.0, text,
        tokens.mapIndexed { index, token -> Token(token, index.toDouble(), index + 1.0) })

    @Test fun ayaEnglishRetainsSpacesAndCommaPlacementWithoutTokenWhitespace() {
        val source = line("Lay, ay, ay, ay", "Lay", ",", "ay", ",", "ay", ",", "ay")
        val parts = lyricParts(source)
        assertEquals(source.text, parts.joinToString("") { it.text })
        assertEquals(listOf("Lay", ",", " ", "ay", ",", " ", "ay", ",", " ", "ay"), parts.map { it.text })
        assertEquals(source.tokens, parts.mapNotNull { it.token })
    }
    @Test fun repeatedWordsMatchOnlyForwardWithoutReusingFirstOccurrence() {
        val parts = lyricParts(line("ay ay, ay", "ay", "ay", "ay"))
        assertEquals(listOf("ay", " ", "ay", ", ", "ay"), parts.map { it.text })
        assertEquals(listOf(0.0, 1.0, 2.0), parts.mapNotNull { it.token?.start })
    }
    @Test fun mixedLanguageWhitespaceAndUntokenizedPunctuationRemainExact() {
        val source = line(" Rain,  rain \u541b\u3068 \u96e8!\n", "Rain", ",", "rain", "\u541b", "\u3068", "\u96e8")
        val parts = lyricParts(source)
        assertEquals(source.text, parts.joinToString("") { it.text })
        assertEquals(6, parts.count { it.token != null })
        assertEquals("!\n", parts.last().text)
    }
    @Test fun anyFailedMatchDiscardsAllPriorHighlightSpans() {
        val source = line("Lay, ay, ay", "Lay", ",", "missing", "ay")
        assertEquals(listOf(LyricPart(source.text)), lyricParts(source))
    }
    @Test fun emptyOrOutOfOrderTokensDisableHighlighting() {
        for (source in listOf(line("Lay, ay", "Lay", ""), line("Lay, ay", "ay", "Lay"), line("Lay, ay", "lay"))) {
            assertEquals(listOf(LyricPart(source.text)), lyricParts(source))
        }
    }
    @Test fun noTokensRenderTheUnmodifiedWholeLine() {
        val source = line("  Lay, ay!  ")
        assertEquals(listOf(LyricPart(source.text)), lyricParts(source))
        assertEquals("", lyricParts(line("")).joinToString("") { it.text })
    }
    @Test fun readingsNeverBecomePartOfTheOriginalLyricText() {
        val token = Token("\u96e8", 0.0, 1.0, "ame")
        val source = Lyric("line", 0.0, 1.0, "\u96e8", listOf(token))
        val parts = lyricParts(source)
        assertEquals(source.text, parts.joinToString("") { it.text })
        assertEquals("ame", parts.single().token?.reading)
    }
}
