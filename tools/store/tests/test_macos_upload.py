import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storelib import GuardError
from upload_macos import check_altool_result


class MacUploadTests(unittest.TestCase):
    def test_explicit_success(self):
        result = {"success-message": "No errors validating archive"}
        self.assertEqual(check_altool_result(json.dumps(result)), result)

    def test_zero_exit_error_body_is_not_success(self):
        with self.assertRaises(GuardError):
            check_altool_result(json.dumps({"product-errors": [{"message": "Validation failed"}]}))

    def test_mixed_success_and_error_is_rejected(self):
        with self.assertRaises(GuardError):
            check_altool_result(json.dumps({"success-message": "ok", "product-errors": ["failure"]}))

    def test_unknown_response_needs_reconciliation(self):
        for raw in ["", "Running altool", "{}", "[]", '{"status":"ok"}']:
            with self.subTest(raw=raw), self.assertRaises(GuardError):
                check_altool_result(raw)
