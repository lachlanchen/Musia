#!/usr/bin/env python3
"""Renew an exhausted idle poll window without replenishing its render budget."""
import argparse
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from musia.creator.billing import private_read
from musia.creator.supervisor import Config, daemon_lock, supervisor_lock


def renew(directory, path, run_id, *, apply=False):
    with daemon_lock(directory), supervisor_lock(directory):
        original = private_read(path)
        old = Config(**json.loads(original))
        if not old.enabled or not old.dispatch or old.review_inputs or run_id == old.run_id:
            raise ValueError('Only an enabled manual-review pilot with a new run ID can renew')
        with sqlite3.connect(f'file:{directory}/supervisor.sqlite?mode=ro', uri=True) as db:
            db.row_factory = sqlite3.Row
            row = db.execute('SELECT * FROM runs WHERE id=?', (old.run_id,)).fetchone()
            if not row or json.loads(row['config']) != asdict(old) or row['passes'] < old.max_passes:
                raise ValueError('The exact previous poll window must be exhausted')
            if db.execute('SELECT 1 FROM runs WHERE id=?', (run_id,)).fetchone():
                raise ValueError('Successor run already exists')
            if db.execute("SELECT 1 FROM attempts WHERE stage='dispatch' AND status='started'").fetchone():
                raise ValueError('Reconcile unresolved dispatch before renewal')
            next_config = replace(old, run_id=run_id,
                max_per_run=old.max_per_run-row['actions'],
                max_dispatches=old.max_dispatches-row['dispatches'])
        with sqlite3.connect(f'file:{directory}/creator.sqlite?mode=ro', uri=True) as db:
            if db.execute("SELECT 1 FROM jobs WHERE state IN ('running','interrupted')").fetchone():
                raise ValueError('Reconcile worker before renewal')
        receipt = {'previousRun': old.run_id, 'next': asdict(next_config), 'applied': False,
                   'renderBudgetReplenished': False, 'inputApproval': 'manual', 'outputApproval': 'manual'}
        if apply:
            if private_read(path) != original:
                raise ValueError('Configuration changed during preflight')
            fd, name = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
            try:
                with os.fdopen(fd, 'w') as stream:
                    json.dump(asdict(next_config), stream, indent=2)
                    stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
                os.replace(name, path)
            finally:
                if os.path.exists(name): os.unlink(name)
            receipt['applied'] = True
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    os.umask(0o077)
    print(json.dumps(renew(args.data, args.config, args.run_id, apply=args.apply), indent=2))


if __name__ == '__main__':
    main()
