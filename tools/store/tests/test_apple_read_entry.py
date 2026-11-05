import datetime as dt
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import apple_read_entry as entry


class EntryTests(unittest.TestCase):
    def test_payload_contains_all_modules_and_compiles(self):
        data = entry.payload(Path(entry.__file__).parent)
        compile(data, "stream", "exec")
        for module in entry.NAMES[:3]: self.assertIn(module.encode(), data)
        self.assertNotIn(b"private_key", data)

    def test_exact_admission(self):
        folder = Path(entry.__file__).parent
        now = dt.datetime.now(dt.timezone.utc)
        a = {"id": "2a1b847d-85c0-4093-9361-ebcc6160d862", "kind": "musia-read-boundary",
             "build": "0.2.2(12)", "route": entry.HOST, "hostUUID": entry.HOST_UUID,
             "source": "pinned", "hashes": {n: entry.digest(folder/n) for n in entry.NAMES},
             "outerSeconds": 100, "remoteSeconds": 60,
             "startBeforeUTC": (now + dt.timedelta(minutes=1)).isoformat()}
        entry.validate(a, folder, "pinned", now)
        for key, bad in (("source", "changed"), ("route", "lazy-macmini"), ("build", "13"),
                         ("outerSeconds", 101), ("hostUUID", "other"), ("hashes", {}),
                         ("startBeforeUTC", (now-dt.timedelta(seconds=1)).isoformat())):
            with self.subTest(key=key), self.assertRaises(AssertionError):
                entry.validate({**a,key:bad}, folder, "pinned", now)


if __name__ == "__main__": unittest.main()
