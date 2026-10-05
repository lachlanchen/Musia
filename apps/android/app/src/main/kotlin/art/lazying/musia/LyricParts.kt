package art.lazying.musia

val defaultLyricLanguages = setOf("en", "zh", "ja")
fun lyricLanguageKey(code: String): String = code.substringBefore('-')
fun lyricLanguageRank(code: String): Int = listOf("en", "zh", "ja", "mul", "yue").indexOf(lyricLanguageKey(code)).let { if (it < 0) 5 else it }
fun lyricLanguageLabel(code: String): String = when (lyricLanguageKey(code)) {
    "en" -> "English"
    "zh" -> "中文"
    "ja" -> "日本語"
    "mul" -> "Original"
    "yue" -> "粵語"
    else -> java.util.Locale.forLanguageTag(code).getDisplayLanguage(java.util.Locale.getDefault()).ifBlank { code }
}

data class LyricPart(val text: String, val token: Token? = null)

fun lyricParts(line: Lyric): List<LyricPart> {
    val parts = mutableListOf<LyricPart>()
    var cursor = 0
    // The original line owns spacing and punctuation; token text only locates spans.
    for (token in line.tokens) {
        val start = line.text.indexOf(token.text, startIndex = cursor)
        if (token.text.isEmpty() || start < 0) return listOf(LyricPart(line.text))
        if (start > cursor) parts += LyricPart(line.text.substring(cursor, start))
        val end = start + token.text.length
        parts += LyricPart(line.text.substring(start, end), token)
        cursor = end
    }
    if (cursor < line.text.length) parts += LyricPart(line.text.substring(cursor))
    return parts
}
