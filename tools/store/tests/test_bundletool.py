import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import install_bundletool as installer
from storelib import GuardError


class BundletoolInstallerTests(unittest.TestCase):
    def test_verified_existing_jar_is_reused_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            jar = Path(directory)/"shared.jar"
            jar.write_bytes(b"test jar")
            with patch.object(installer,"SHA256",hashlib.sha256(b"test jar").hexdigest()), \
                 patch.object(sys,"argv",["installer","--existing",str(jar)]), \
                 patch.object(installer.urllib.request,"urlopen") as network:
                installer.main()
                network.assert_not_called()

    def test_wrong_existing_jar_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            jar = Path(directory)/"shared.jar"
            jar.write_bytes(b"unexpected")
            with patch.object(sys,"argv",["installer","--existing",str(jar)]), \
                 patch.object(installer.urllib.request,"urlopen") as network:
                with self.assertRaises(GuardError):
                    installer.main()
                network.assert_not_called()
            self.assertEqual(jar.read_bytes(),b"unexpected")

    def test_bad_download_never_promotes_a_jar(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(Path,"home",return_value=Path(directory)), \
                 patch.object(sys,"argv",["installer"]), \
                 patch.object(installer.urllib.request,"urlopen",return_value=io.BytesIO(b"bad download")):
                with self.assertRaises(GuardError):
                    installer.main()
            self.assertEqual(list(Path(directory).rglob("*.jar")),[])


if __name__ == "__main__":
    unittest.main()
