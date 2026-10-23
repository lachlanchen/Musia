#!/usr/bin/env python3
"""Three synthetic text-provider checks; no account, audio render or publication."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from musia.creator.agent import Producer
from musia.creator.context import prepare
from musia.creator.contracts import Chat, Draft, SongReference
from musia.creator.store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confirm-provider-calls', action='store_true')
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    if not args.confirm_provider_calls:
        parser.error('Requires explicit consent to three text-provider requests')
    os.umask(0o077)
    args.evidence.mkdir(parents=True, exist_ok=False)
    producer = Producer()
    assert producer.available, 'No configured text provider'
    brief = Draft(title='The Window Left Open', bpm=82)
    cases = [
        Chat(message='Keep this title and tempo. Ask one short question about the emotional image for an intimate song. No lyrics yet, no render.', brief=brief),
        Chat(message='I am a beginner. Explain this excerpt and one gentle guitar practice at a slower tempo. Do not change my draft or grade my ability.',
             brief=brief, focus='learn', reference=SongReference(source='catalog', id='first-pulse', position=4)),
        Chat(message='What are the exact chords in my new recording? If there is no recording evidence, explain what is missing. Do not guess.',
             brief=brief, focus='analyze'),
    ]
    records = []
    try:
        with tempfile.TemporaryDirectory(prefix='musia-context-canary-') as directory:
            store = Store(Path(directory))
            for request in cases:
                start = time.monotonic()
                reply = producer.refine(prepare(request, store, 'synthetic-no-account'))
                assert reply.brief == brief, 'Draft changed during a discussion'
                records.append({'focus': request.focus, 'seconds': round(time.monotonic()-start, 2),
                                'reply': reply.model_dump(), 'draftPreserved': True})
                print(json.dumps({'focus': request.focus, 'seconds': records[-1]['seconds'], 'validReply': True}), flush=True)
    finally:
        (args.evidence / 'result.json').write_text(json.dumps({'backend': producer.backend,
            'model': producer.model, 'callsCompleted': len(records), 'rendered': False,
            'accountAccessed': False, 'cases': records}, ensure_ascii=False, indent=2) + '\n')
    assert len(records) == 3


if __name__ == '__main__':
    main()
