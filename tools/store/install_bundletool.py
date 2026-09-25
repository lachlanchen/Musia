#!/usr/bin/env python3
"""Install one checksum-pinned shared bundletool, optionally configure Musia."""
import argparse
import hashlib
import os
from pathlib import Path
import tempfile
import urllib.request

from storelib import RUNTIME, config, digest, require, write_private

VERSION = "1.18.3"
SHA256 = "a099cfa1543f55593bc2ed16a70a7c67fe54b1747bb7301f37fdfd6d91028e29"
URL = f"https://github.com/google/bundletool/releases/download/{VERSION}/bundletool-all-{VERSION}.jar"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configure", action="store_true")
    parser.add_argument("--existing", type=Path, help="Reuse a verified standalone JAR instead of downloading")
    args = parser.parse_args()
    target = args.existing or Path.home()/".local/share/android-tools/bundletool"/VERSION/"bundletool.jar"
    if not target.exists():
        require(not args.existing, "The supplied shared bundletool does not exist")
        target.parent.mkdir(parents=True,exist_ok=True)
        name = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent,delete=False) as temporary:
                name = temporary.name
                checksum = hashlib.sha256()
                total = 0
                with urllib.request.urlopen(URL,timeout=60) as source:
                    while block := source.read(1024*1024):
                        total += len(block)
                        require(total <= 64*1024*1024,"Unexpected bundletool size")
                        temporary.write(block)
                        checksum.update(block)
                require(checksum.hexdigest() == SHA256,"Downloaded bundletool checksum mismatch")
            require(not target.exists(),"Another installer supplied this path; retry to verify it")
            os.replace(name,target)
        finally:
            if name and Path(name).exists():
                Path(name).unlink()
    require(target.is_file() and not target.is_symlink() and digest(target) == SHA256,"Existing bundletool checksum mismatch")
    if args.configure:
        settings = config()
        settings.update(bundletool_jar=str(target.resolve()),bundletool_sha256=SHA256)
        write_private(Path(os.environ.get("MUSIA_STORE_CONFIG",RUNTIME/"config.json")).expanduser(),settings)
    print(f"Verified bundletool {VERSION}: {target}")


if __name__ == "__main__":
    main()
