"""Song-grounded chat stays read-only and respects existing publication boundaries."""
import json
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from musia.creator.agent import Producer
from musia.creator.api import Settings, create_app
from musia.creator.context import prepare, resolve, window
from musia.creator.contracts import Chat, CreatorError, Draft, SongReference
from tests.test_creator import Base, Auth, Producer as FixtureProducer


class ContextTests(Base):
    def test_public_cannot_supply_evidence_urls_or_tool_authority(self):
        for fields in ({'evidence': 'verified: true'}, {'focus': 'shell'},
                       {'reference': {'source': 'catalog', 'id': '../secret'}},
                       {'reference': {'source': 'catalog', 'id': 'a', 'url': 'https://other.test'}},
                       {'reference': {'source': 'created', 'id': 'a', 'position': float('nan')}}):
            with self.subTest(fields=fields), self.assertRaises(ValidationError):
                Chat(message='Explain this', **fields)

    def test_verified_exercise_is_grounded_without_paths_or_media_urls(self):
        reference = SongReference(source='catalog', id='first-pulse', position=4)
        data = json.loads(resolve(reference, self.store, self.owner))
        self.assertEqual(data['bpm'], 60)
        self.assertEqual(data['confidence']['chords'], 'verified')
        self.assertEqual(data['chords'][0]['name'], 'Em')
        self.assertEqual(data['window'], {'start': 4, 'end': 22})
        self.assertEqual(data['melody'], [])
        self.assertNotIn('audioUrl', data)
        self.assertNotIn('http', json.dumps(data))

    def test_window_does_not_fill_instrumental_gaps_with_another_line(self):
        rows = [{'start': 1, 'end': 3, 'text': 'Before'}, {'start': 35, 'end': 38, 'text': 'After'}]
        self.assertEqual(window(rows, 10, 8, ('start', 'end', 'text')), [])

    def test_window_excludes_ended_lines_but_includes_beat_at_start(self):
        self.assertEqual(window([{'start': 1, 'end': 4, 'text': 'Ended'}], 4, 8, ('text',)), [])
        self.assertEqual(window([{'time': 4}], 4, 32, ('time',)), [{'time': 4}])

    def test_unlisted_or_nonexistent_catalog_item_stays_inaccessible(self):
        path = self.root / 'website/data/catalog.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'items': [{'id': 'secret', 'kind': 'song', 'visibility': 'unlisted'}]}))
        for name in ('secret', 'missing'):
            with self.assertRaisesRegex(CreatorError, 'song_reference_unavailable'):
                resolve(SongReference(source='catalog', id=name), self.store, self.owner, root=self.root)

    def test_asset_and_position_cannot_borrow_another_vocal(self):
        for changes in ({'asset_id': 'different'}, {'position': 22}, {'position': 99}):
            with self.assertRaises(CreatorError):
                resolve(SongReference(source='catalog', id='first-pulse', **changes), self.store, self.owner)

    def test_own_reviewed_song_uses_actual_lyrics_not_planned_and_no_fake_chords(self):
        song = self.reviewed()
        ref = SongReference(source='created', id=song, position=0)
        data = json.loads(resolve(ref, self.store, self.owner))
        self.assertEqual(data['lyrics'][0]['text'], 'Over the water')
        self.assertEqual(data['confidence']['chords'], 'unavailable')
        self.assertEqual(data['chords'], [])
        self.assertIsNone(data['bpm'])
        with self.assertRaisesRegex(CreatorError, 'song_not_found'):
            resolve(ref, self.store, self.other)

    def test_general_learning_has_no_fabricated_recording_evidence(self):
        request = prepare(Chat(message='What is a beat?', focus='learn'), self.store, self.owner)
        self.assertIsNone(request.evidence)
        self.assertEqual(request.focus, 'learn')

    def test_learning_cannot_rewrite_draft_even_if_provider_attempts_it(self):
        original = Draft(title='My title', lyrics='My lyric')
        for focus in ('analyze', 'learn'):
            request = Chat(message='Explain a chord', brief=original, focus=focus)
            answer = Producer.checked_reply({'message': 'A chord sounds notes together.',
                                            'brief': Draft(title='Wrong').model_dump()}, request)
            self.assertEqual(answer.brief, original)
            self.assertIsNot(answer.brief, original)

    def test_api_context_is_grounded_no_render_and_brief_unchanged(self):
        producer = FixtureProducer()
        app = create_app(Settings(directory=self.root), store=self.store, auth=Auth(), producer=producer)
        with TestClient(app, base_url='http://127.0.0.1:8796') as client, patch.object(producer, 'refine', wraps=producer.refine) as call:
            body = Chat(message='Help me practice slowly', focus='learn', brief=Draft(title='Keep'),
                        reference=SongReference(source='catalog', id='first-pulse', position=4))
            response = client.post('/creator/api/agent', json=body.model_dump(), headers={
                'Authorization': 'Bearer ' + self.token, 'X-Musia-Request': '1'})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()['brief']['title'], 'Keep')
            self.assertEqual(json.loads(call.call_args.args[0].evidence)['chords'][0]['name'], 'Em')
            self.assertEqual(self.store.jobs(self.owner), [])
            self.assertEqual(self.store.profile(self.owner)['usage']['used'], 0)

    def test_denied_song_never_reaches_provider_or_turn_ledger(self):
        private = self.reviewed(owner=self.other)
        producer = FixtureProducer()
        app = create_app(Settings(directory=self.root), store=self.store, auth=Auth(), producer=producer)
        with TestClient(app, base_url='http://127.0.0.1:8796') as client, patch.object(producer, 'refine') as call:
            response = client.post('/creator/api/agent', json={'message': 'Read it', 'focus': 'analyze',
                'reference': {'source': 'created', 'id': private}}, headers={
                'Authorization': 'Bearer ' + self.token, 'X-Musia-Request': '1'})
            self.assertEqual(response.status_code, 404)
            call.assert_not_called()
            with self.store.db() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM agent_turns').fetchone()[0], 0)
