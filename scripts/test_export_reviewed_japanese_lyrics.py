import unittest

from export_reviewed_japanese_lyrics import chinese_tokens, japanese_tokens, reviewed_words


class ReviewedJapaneseTests(unittest.TestCase):
    def setUp(self):
        self.sources = {"a": {"segments": [{"words": [
            {"word": "君", "start": 1.0, "end": 1.5},
            {"word": "の", "start": 1.5, "end": 1.7},
            {"word": "話", "start": 1.7, "end": 2.2},
        ]}]}}
        self.row = {"anchors": [{"source": "a", "segment": 0}], "ja": "君の話"}

    def test_preserves_anchors(self):
        words = reviewed_words(self.row, self.sources)
        self.assertEqual((words[0]["start"], words[-1]["end"]), (1.0, 2.2))

    def test_explicit_reviewed_replacement(self):
        self.row.update(ja="あなたの話", replacements=[{
            "words": [0, 1], "source": "君", "text": "あなた", "reason": "Test reviewed phrase"}])
        self.assertEqual(reviewed_words(self.row, self.sources)[0]["end"], 1.5)
        self.assertEqual(self.sources["a"]["segments"][0]["words"][0]["word"], "君")

    def test_rejects_unreviewed_text(self):
        self.row["ja"] = "あなたの話"
        with self.assertRaises(ValueError):
            reviewed_words(self.row, self.sources)

    def test_rejects_wrong_replacement_evidence(self):
        self.row["replacements"] = [{"words": [0, 1], "source": "彼", "text": "君", "reason": "wrong"}]
        with self.assertRaises(ValueError):
            reviewed_words(self.row, self.sources)

    def test_rejects_empty_word_timing(self):
        self.sources["a"]["segments"][0]["words"][0]["end"] = 1.0
        with self.assertRaises(ValueError):
            reviewed_words(self.row, self.sources)

    def test_reviewed_merge_can_absorb_zero_length_subtoken(self):
        self.sources["a"]["segments"][0]["words"][0]["end"] = 1.0
        self.row["replacements"] = [{"words": [0, 2], "source": "君の", "text": "君の",
                                     "reason": "Merge an ASR subtoken into its enclosing positive span"}]
        words = reviewed_words(self.row, self.sources)
        self.assertEqual((words[0]["start"], words[0]["end"]), (1.0, 1.7))

    def test_rejects_out_of_bounds(self):
        self.row["anchors"][0]["words"] = [0, 4]
        with self.assertRaises(ValueError):
            reviewed_words(self.row, self.sources)

    def test_reading_override_and_timing(self):
        import pykakasi
        tokens = japanese_tokens(reviewed_words(self.row, self.sources), pykakasi.kakasi(), {"君": "きみ"})
        self.assertEqual(tokens[0]["reading"], "きみ")
        self.assertEqual("".join(t["text"] for t in tokens), "君の話")
        self.assertEqual(tokens[-1]["end"], 2.2)

    def test_contextual_chinese_reading(self):
        tokens = chinese_tokens("挥着手", [{"index": 1, "text": "着", "pinyin": "zhe5"}])
        self.assertEqual(tokens[1]["pinyin"], "zhe5")

    def test_rejects_stale_chinese_override(self):
        with self.assertRaises(ValueError):
            chinese_tokens("挥着手", [{"index": 0, "text": "着", "pinyin": "zhe5"}])

    def test_chinese_translation_preserves_latin_and_punctuation(self):
        text = "Aya，欢迎回来！"
        tokens = chinese_tokens(text, [])
        self.assertEqual("".join(token["text"] for token in tokens), text)
        self.assertEqual(tokens[-2]["pinyin"], "lai2")


if __name__ == "__main__":
    unittest.main()
