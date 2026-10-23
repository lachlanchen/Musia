"""Resolve song IDs through existing access rules, never client URLs or files."""

import json

from musia.learning import PublicLibrary, ROOT, first_pulse
from .contracts import CreatorError, ProducerRequest


def window(rows, position, limit, keys):
    return [{key: row[key] for key in keys if key in row}
            for row in rows if (row['end'] > position if 'end' in row else row.get('time', 0) >= position)
            and row.get('start', row.get('time', 0)) < position + 20][:limit]


def resolve(reference, store, owner, *, root=ROOT):
    if reference.source == 'created':
        song = store.song(reference.id, owner)  # Includes private ownership and block checks.
        if reference.asset_id not in (None, 'creator-audio'):
            raise CreatorError('song_reference_unavailable', 404)
        asset = {'id': 'creator-audio', 'language': song['language'], 'duration': song['duration'],
                 'lyrics': song['lyricLines'], 'confidence': {
                     'beats': 'unavailable', 'chords': 'unavailable', 'melody': 'unavailable'}}
    else:
        library = PublicLibrary(root)
        if reference.id == 'first-pulse':
            song = first_pulse('https://musia.lazying.art')
        else:
            item = next((item for item in library.entries() if item['id'] == reference.id), None)
            song = library.song(item) if item else None
        if not song:
            raise CreatorError('song_reference_unavailable', 404)
        asset = next((asset for asset in song['assets']
                      if asset['id'] == (reference.asset_id or song['defaultAssetId'])), None)
        if not asset:
            raise CreatorError('song_reference_unavailable', 404)
    if reference.position >= asset['duration']:
        raise CreatorError('song_position_out_of_range', 422)
    lyrics = asset.get('lyrics', [])
    evidence = {
        'source': reference.source, 'id': reference.id, 'title': song['title'],
        'assetId': asset['id'], 'language': asset['language'], 'duration': asset['duration'],
        'window': {'start': reference.position, 'end': min(reference.position + 20, asset['duration'])},
        'bpm': asset.get('bpm'), 'timeSignature': asset.get('timeSignature'),
        'confidence': asset['confidence'], 'lyricLineCount': len(lyrics),
        'lyrics': window(lyrics, reference.position, 8, ('start', 'end', 'text')),
        'chords': window(asset.get('chords', []), reference.position, 12, ('start', 'end', 'name', 'confidence')),
        'beats': window(asset.get('beats', []), reference.position, 32, ('time',)),
        'melody': window(asset.get('melody', []), reference.position, 16, ('start', 'end', 'note')),
        'limitations': 'Saved data only, not new audio analysis. A capped 20-second excerpt, not the full score. '
                        'No audio was sent or listened to by the chat model. Missing fields are unknown; '
                        'analysis/estimated confidence is not a verified score or a performance grade.'}
    # Long lyric lines are excerpted, never promoted to a complete transcription.
    for line in evidence['lyrics']:
        if len(line['text']) > 240:
            line['text'] = line['text'][:240] + ' [excerpt]'
    text = json.dumps(evidence, ensure_ascii=False, separators=(',', ':'))
    if len(text) > 8000:
        raise CreatorError('song_context_too_large', 422)
    return text


def prepare(request, store, owner, *, root=ROOT):
    evidence = resolve(request.reference, store, owner, root=root) if request.reference else None
    prepared = ProducerRequest(**request.model_dump(), evidence=evidence)
    while len(prepared.model_dump_json().encode()) > 45000:
        if not prepared.history:
            raise CreatorError('song_context_too_large', 422)
        prepared.history = prepared.history[1:]
    return prepared
