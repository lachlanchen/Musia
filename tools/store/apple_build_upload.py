#!/usr/bin/env python3
"""Upload an inspected Apple binary from Linux after native cleanup and QA.

No review, price or account mutations. Every mutation is journaled before sending;
unknown outcomes are readback-only. See Apple's Build uploads API collection.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit

import jwt
import requests

import storelib as s
from creator_apple_screenshot import isolated_session, response_diagnostic

APP = '6816265930'
API = 'https://api.appstoreconnect.apple.com'


def upload_parts(operations, size, now):
    s.require(isinstance(operations, list) and 0 < len(operations) <= 200, 'Invalid upload operations')
    cursor = 0
    parts = sorted(operations, key=lambda op: op['offset'])
    for part in parts:
        url = urlsplit(part['url'])
        s.require(part['method'] == 'PUT' and url.scheme == 'https'
                  and url.hostname == 'northamerica-1.object-storage.apple.com'
                  and url.port in (None, 443) and not url.username and not url.password and not url.fragment,
                  'Unexpected upload destination')
        s.require(type(part['offset']) is int and type(part['length']) is int
                  and part['offset'] == cursor and part['length'] > 0, 'Invalid upload range')
        cursor += part['length']
        expiry = dt.datetime.fromisoformat(part['expiration'].replace('Z', '+00:00'))
        s.require(expiry.tzinfo and expiry > now, 'Expired upload operation')
        headers = part['requestHeaders']
        s.require(isinstance(headers, list) and len(headers) <= 10
                  and all(h['name'].lower() in {'content-type', 'content-md5'}
                          and '\n' not in h['value'] and '\r' not in h['value'] for h in headers), 'Unexpected upload header')
    s.require(cursor == size, 'Upload ranges do not cover exact artifact')
    return parts


class BuildAPI(s.Apple):
    def __init__(self, journal):
        super().__init__()
        self.journal = journal
        self.session = isolated_session()

    def mutate(self, method, path, body, step):
        s.require((method == 'POST' and path in {'/v1/buildUploads', '/v1/buildUploadFiles'})
                  or (method == 'PATCH' and re.fullmatch(r'/v1/buildUploadFiles/[A-Za-z0-9-]+', path)),
                  'Only binary upload mutations allowed')
        state = s.read_json(self.journal)
        s.require(step not in state['steps'], 'Mutation attempted already; reconcile GET only')
        state['steps'][step] = {'state': 'started', 'at': s.now(), 'path': path}
        s.write_private(self.journal, state)
        key = s.private_file(self.cfg['asc_key_path'])
        token = jwt.encode({'iss': self.cfg['asc_issuer'], 'iat': int(time.time()),
                            'exp': int(time.time()) + 600, 'aud': 'appstoreconnect-v1'},
                           key.read_text(), algorithm='ES256', headers={'kid': self.cfg['asc_key_id']})
        try:
            response = self.session.request(method, API + path, json=body,
                       headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
                       timeout=(10, 45), allow_redirects=False)
            diagnostic, result = response_diagnostic(response)
            state['steps'][step].update(diagnostic=diagnostic)
            s.write_private(self.journal, state)
            s.require(200 <= response.status_code < 300 and isinstance(result, dict),
                      'Apple upload mutation unconfirmed; reconcile private journal')
        except requests.RequestException:
            raise s.GuardError('Apple upload result unknown; GET reconciliation only') from None
        state['steps'][step].update(state='accepted', response=result)
        s.write_private(self.journal, state)
        return result['data']


def qualify_cleanup(manifest, native, handback):
    s.require(native['state'] == 'native_passed_pending_visual_review_and_provider_upload'
              and not native.get('error'), 'Native qualification incomplete')
    s.require(handback.get('admission') == native['admission'] and handback.get('guardAbsent')
              and handback.get('ownedChildrenAbsent') and handback.get('preservationVerified'),
              'Actual independent handback missing')
    if 'cleanup_recovery' not in manifest:
        s.require(native.get('guardReleased') and native.get('preservationVerified')
                  and not native.get('cleanupError'), 'Native cleanup incomplete')
        return

    # A later cleanup receipt supplements the immutable native result; it cannot
    # turn a failed build into a pass or qualify a different artifact.
    s.require(native.get('guardReleased') is False and native.get('cleanupError') ==
              'RuntimeError: Unexplained native processes; retain guard without signals',
              'Unsupported cleanup recovery')
    reference = manifest['cleanup_recovery']
    s.require(s.digest(s.private_file(reference['path'])) == reference['sha256'], 'Changed cleanup recovery')
    recovery = s.read_json(reference['path'])
    for proof in (recovery, handback):
        s.require(proof.get('passed') is True and proof.get('guardReleased') is True
                  and proof.get('guardAbsent') is True and proof.get('preservationVerified') is True
                  and proof.get('ownedChildrenAbsent') is True and not proof.get('error'),
                  'Cleanup proof incomplete')
        s.require(proof.get('admission') == native['admission'] and proof.get('source') == manifest['source']
                  and proof.get('nativeResultSha256') == manifest['native_result']['sha256']
                  and proof.get('artifactSha256') == manifest['artifact']['sha256'], 'Cleanup proof binding mismatch')
        reconciliation = proof.get('processReconciliation', {})
        s.require(reconciliation.get('passed') is True and reconciliation.get('recordedChildrenComplete') is True
                  and reconciliation.get('liveOwned') == [] and reconciliation.get('unexplainedProcesses') == [],
                  'Cleanup process reconciliation incomplete')
    s.require(recovery.get('readOnly') is False and handback.get('readOnly') is True
              and handback.get('recoverySha256') == reference['sha256'], 'Independent recovery verification missing')
    try:
        native_end, recovered, independently_started = [dt.datetime.fromisoformat(v.replace('Z', '+00:00'))
            for v in (native['ended'], recovery['ended'], handback['started'])]
        ordered = all(t.tzinfo is not None for t in (native_end, recovered, independently_started)) and \
            native_end <= recovered <= independently_started
    except (KeyError, TypeError, ValueError):
        ordered = False
    s.require(ordered, 'Cleanup recovery chronology invalid')


def qualify(manifest_path):
    manifest = s.read_json(s.private_file(manifest_path))
    s.require(manifest['app_id'] == APP and manifest['bundle_id'] == s.BUNDLE
              and manifest['version'] == s.release()['version'] and manifest['build'] == s.release()['ios_build'], 'Wrong release')
    s.require(manifest['platform'] in {'IOS', 'MAC_OS'}, 'Wrong platform')
    for name in ('artifact', 'native_result', 'independent_handback', 'inspection', 'qa'):
        s.require(s.digest(s.private_file(manifest[name]['path'])) == manifest[name]['sha256'], 'Changed ' + name)
    native = s.read_json(manifest['native_result']['path'])
    s.require(native.get('source') == manifest['source']
              and native.get('artifact', {}).get('sha256') == manifest['artifact']['sha256']
              and native.get('artifact', {}).get('inspectionSha256') == manifest['inspection']['sha256'], 'Native artifact binding changed')
    handback = s.read_json(manifest['independent_handback']['path'])
    qualify_cleanup(manifest, native, handback)
    qa = s.read_json(manifest['qa']['path'])
    s.require(qa.get('source') == manifest['source'] and qa.get('artifact_sha256') == manifest['artifact']['sha256']
              and qa.get('scope') == 'internal-owner-test' and qa.get('visual_reviewed') is True
              and qa.get('known_limitations') and qa.get('production_qualified') is False, 'Internal visual QA missing')
    inspection = s.read_json(manifest['inspection']['path'])
    s.require(inspection.get('bundle_id') == s.BUNDLE and inspection.get('version') == manifest['version']
              and str(inspection.get('build_number', inspection.get('build'))) == manifest['build'], 'Inspected version mismatch')
    if manifest['platform'] == 'IOS':
        s.require(native.get('nativeUIPassed') and inspection.get('state') == 'signed'
                  and inspection.get('artifact_sha256') == manifest['artifact']['sha256']
                  and inspection.get('identity', {}).get('certificate_sha1') == s.config()['apple_certificate_sha1'], 'iOS signer/QA mismatch')
    else:
        s.require(native.get('macCompilePassed') and inspection.get('package_sha256') == manifest['artifact']['sha256']
                  and inspection.get('signer_sha1') == s.config()['apple_certificate_sha1']
                  and sorted(inspection.get('architectures', [])) == ['arm64', 'x86_64'], 'Mac signer/architectures mismatch')
    return manifest


def upload(manifest_path, confirm=False):
    manifest = qualify(manifest_path)
    journal = s.RUNTIME / 'operations' / ('apple-build-upload-' + manifest['platform'] + '-' + manifest['artifact']['sha256'] + '.json')
    with s.lock('apple-upload'):
        api = BuildAPI(journal)
        s.require(api.app()['id'] == APP, 'Wrong Apple app')
        s.require(not s.apple_platform_builds(api, APP, manifest['build'], manifest['platform']), 'Build exists; reconcile instead')
        reservations = [r for r in api.rows('/v1/apps/' + APP + '/buildUploads?limit=200')
                        if r['attributes']['cfBundleVersion'] == manifest['build'] and r['attributes']['platform'] == manifest['platform']]
        s.require(len(reservations) <= 1, 'Ambiguous reservation')
        if not confirm:
            return dict(state='qualified_plan', platform=manifest['platform'], reservation_count=len(reservations))
        s.require(not journal.exists(), 'Upload already attempted; GET reconciliation only')
        data = Path(manifest['artifact']['path']).read_bytes()
        s.require(hashlib.sha256(data).hexdigest() == manifest['artifact']['sha256'], 'Artifact changed')
        s.write_private(journal, dict(at=s.now(), manifest=manifest, steps={}, parts=[]))
        if reservations:
            reservation = reservations[0]
            s.require(reservation['attributes']['cfBundleShortVersionString'] == manifest['version']
                      and reservation['attributes']['state']['state'] == 'AWAITING_UPLOAD'
                      and not api.rows('/v1/buildUploads/' + reservation['id'] + '/buildUploadFiles'),
                      'Reservation already used; reconcile')
        else:
            reservation = api.mutate('POST', '/v1/buildUploads', {'data': {'type': 'buildUploads',
                'attributes': {'cfBundleShortVersionString': manifest['version'], 'cfBundleVersion': manifest['build'], 'platform': manifest['platform']},
                'relationships': {'app': {'data': {'type': 'apps', 'id': APP}}}}}, 'reserve')
        state = s.read_json(journal); state['buildUploadId'] = reservation['id']; s.write_private(journal, state)
        kind = ('Musia.ipa', 'com.apple.ipa') if manifest['platform'] == 'IOS' else ('Musia.pkg', 'com.apple.pkg')
        file = api.mutate('POST', '/v1/buildUploadFiles', {'data': {'type': 'buildUploadFiles',
            'attributes': {'assetType': 'ASSET', 'fileName': kind[0], 'fileSize': len(data), 'uti': kind[1]},
            'relationships': {'buildUpload': {'data': {'type': 'buildUploads', 'id': reservation['id']}}}}}, 'file')
        state = s.read_json(journal); state['fileId'] = file['id']; s.write_private(journal, state)
        parts = upload_parts(file['attributes']['uploadOperations'], len(data), dt.datetime.now(dt.timezone.utc))
        blob = isolated_session()
        for index, part in enumerate(parts):
            state = s.read_json(journal)
            state['parts'].append(dict(index=index, state='started', offset=part['offset'], length=part['length']))
            s.write_private(journal, state)
            try:
                response = blob.put(part['url'], data=data[part['offset']:part['offset'] + part['length']],
                                    headers={h['name']: h['value'] for h in part['requestHeaders']},
                                    timeout=(15, 180), allow_redirects=False)
                s.require(200 <= response.status_code < 300, 'Part unconfirmed; GET reconciliation only')
            except requests.RequestException:
                raise s.GuardError('Part result unknown; GET reconciliation only') from None
            state['parts'][-1].update(state='accepted', http=response.status_code); s.write_private(journal, state)
        committed = api.mutate('PATCH', '/v1/buildUploadFiles/' + file['id'], {'data': {'type': 'buildUploadFiles', 'id': file['id'],
            'attributes': {'uploaded': True, 'sourceFileChecksums': {'file': {'algorithm': 'MD5', 'hash': hashlib.md5(data).hexdigest()}}}}}, 'commit')
        state = s.read_json(journal); state['assetDeliveryState'] = committed['attributes']['assetDeliveryState']; s.write_private(journal, state)
        return dict(state='uploaded_processing_unverified', platform=manifest['platform'], build=manifest['build'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--confirm-upload', action='store_true')
    args = parser.parse_args()
    print(json.dumps(upload(args.manifest, args.confirm_upload), indent=2))
