"""Prepare one sanitized public song for catalog_add.py; no remote mutation."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('media_id')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    deploy = load('catalog_exporter', ROOT / 'scripts/deploy_musia_learning.py')
    learning = load('learning_projection', ROOT / 'musia/learning.py')
    remote = load('catalog_add', ROOT / 'deploy/learning/catalog_add.py')
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory)
        songs = deploy.export_catalog(learning, target)
        song = next((s for s in songs if s['id'] == args.media_id), None)
        if not song:
            raise ValueError('Song is not eligible for the public Musia catalog')
        items = json.loads((target / 'website/data/catalog.json').read_text())['items']
        packet = {'mediaId': args.media_id, 'song': song,
                  'item': next(i for i in items if i['id'] == args.media_id),
                  'files': {str(p.relative_to(target)): json.loads(p.read_text())
                            for p in (target / 'website/data/songs' / args.media_id).rglob('*.json')}}
        remote.validate_packet(packet)
        raw = remote.encode(packet)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as output:
        output.write(raw)
    print(json.dumps({'packet': str(args.output), 'sha256': hashlib.sha256(raw).hexdigest(),
                      'mediaId': args.media_id, 'bytes': len(raw)}))


if __name__ == '__main__':
    main()
