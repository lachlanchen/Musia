import unittest

from export_reviewed_japanese_lyrics import japanese_tokens, reviewed_words


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


if __name__ == "__main__":
    unittest.main()
