import tempfile
import unittest
from pathlib import Path

from prepare_reviewed_japanese_fun_item import copy_unchanged, prepare, publication_fields


class ReleaseGuardsTests(unittest.TestCase):
    def test_preview_is_unlisted_not_legacy(self):
        self.assertEqual(publication_fields("preview"),
                         {"visibility": "unlisted", "stage": "preview", "listed": False})

    def test_published_remains_listed(self):
        self.assertEqual(publication_fields("published"),
                         {"visibility": "public", "stage": "published", "listed": True})

    def test_unknown_stage_fails_before_io(self):
        with self.assertRaises(ValueError):
            prepare({"mediaId": "test-song", "releaseStage": "typo"})

    def test_rejects_path_as_id_before_io(self):
        with self.assertRaises(ValueError):
            prepare({"mediaId": "../outside"})

    def test_preserves_versioned_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            target = Path(directory) / "nested/target"
            source.write_bytes(b"selected audio")
            copy_unchanged(source, target)
            copy_unchanged(source, target)
            source.write_bytes(b"different audio")
            with self.assertRaises(FileExistsError):
                copy_unchanged(source, target)
            self.assertEqual(target.read_bytes(), b"selected audio")


if __name__ == "__main__":
    unittest.main()
