import copy
import json
import re
import unittest
from pathlib import Path

from scripts.curate_fun_catalog import apply_entry, musical_identity, plan


ROOT = Path(__file__).resolve().parents[1]


class CatalogCurationTest(unittest.TestCase):
    def setUp(self):
        self.group = {"id": "test-song", "titles": {"zh-Hans": "测试曲", "en": "Test Song", "ja": "テスト"}}
        self.item = {"id": "test-song", "title": "Test Song V2"}
        self.manifest = {"id": "test-song", "duration": 12, "timeline": {"lines": [{"start": 1, "text": "Hi"}]},
                         "lyricSets": [{"id": "zh", "tracks": [{"path": "lyrics/zh.json"}]}],
                         "assets": {"primaryAudio": {"id": "zh", "languageCode": "zh-Hans", "src": "zh.mp3"},
                                    "alternateAudio": [{"id": "en", "languageCode": "en", "src": "en.mp3"},
                                                       {"id": "old-zh", "languageCode": "zh-Hans", "src": "old.mp3"}]}}

    def test_bilingual_title_and_musical_identity(self):
        before = copy.deepcopy(musical_identity(self.manifest))
        apply_entry(self.item, self.manifest, self.group, "selected")
        self.assertEqual(self.item["title"], "测试曲 · Test Song")
        self.assertEqual(self.manifest["displayTitle"], self.item["title"])
        self.assertEqual(before, musical_identity(self.manifest))

    def test_keep_other_languages_hide_same_language_take(self):
        apply_entry(self.item, self.manifest, self.group, "selected")
        english, old = self.manifest["assets"]["alternateAudio"]
        self.assertNotIn("hidden", english)
        self.assertEqual(english["label"], "English")
        self.assertTrue(old["hidden"])
        self.assertEqual(old["label"], "中文 · Archive 01")

    def test_archive_is_idempotent_and_keeps_url(self):
        apply_entry(self.item, self.manifest, self.group, "archive", 2)
        before = copy.deepcopy((self.item, self.manifest))
        apply_entry(self.item, self.manifest, self.group, "archive", 2)
        self.assertEqual(before, (self.item, self.manifest))
        self.assertEqual(self.item["title"], "测试曲 · Test Song · Archive 02")
        self.assertFalse(self.manifest["publication"]["listed"])
        self.assertEqual(self.manifest["assets"]["primaryAudio"]["src"], "zh.mp3")

    def test_preview_remains_unlisted(self):
        self.item.update(visibility="unlisted", releaseStage="preview")
        self.manifest["publication"] = {"visibility": "unlisted", "stage": "preview", "listed": False}
        apply_entry(self.item, self.manifest, self.group, "preview")
        self.assertEqual(self.item["visibility"], "unlisted")
        self.assertFalse(self.manifest["publication"]["listed"])

    def test_no_implicit_promotion(self):
        self.item["hidden"] = True
        with self.assertRaisesRegex(ValueError, "promotion"):
            apply_entry(self.item, self.manifest, self.group, "selected")

    def test_reviewed_whole_catalog(self):
        updates = plan(ROOT)
        catalog = updates[ROOT / "website/data/catalog.json"]
        visible = [i for i in catalog["items"] if not i.get("hidden") and i.get("visibility", "public") == "public"]
        songs = [i for i in visible if i["kind"] != "mv"]
        self.assertEqual(len(songs), len({i["workId"] for i in songs}))
        for item in catalog["items"]:
            self.assertRegex(item["title"], r"[\u4e00-\u9fff].* · [A-Za-z]")
            self.assertIsNone(re.search(r"\b(?:ACE|MiniMax|SoulX|DiffRhythm|DR|V\d+)\b", item["title"], re.I))
            self.assertEqual(item["title"], updates[ROOT / "website" / item["manifest"]]["title"])
        self.assertIn("ban-qu-chang-an-ace-changfeng", {i["id"] for i in visible})
        self.assertNotIn("ban-qu-chang-an", {i["id"] for i in visible})
        self.assertIn("xia-ke-xing-original-poem", {i["id"] for i in visible})
        self.assertNotIn("xia-ke-xing", {i["id"] for i in visible})


if __name__ == "__main__":
    unittest.main()
