#!/usr/bin/env python3
"""Reconcile an API upload and attach its VALID build to the existing internal group."""
import argparse
import hashlib
import json
from pathlib import Path

import storelib as s
from apple_build_upload import APP, qualify
from invite_macos import formal_attachments
from musia_store import apple_owner_tester


def deliver(manifest_path, confirm=False):
    manifest = qualify(manifest_path)
    path = s.RUNTIME / 'operations' / ('apple-build-upload-' + manifest['platform'] + '-' + manifest['artifact']['sha256'] + '.json')
    upload = s.read_json(s.private_file(path))
    s.require(upload['manifest'] == manifest and upload.get('fileId') and upload.get('buildUploadId'), 'Upload identity missing')
    api = s.Apple()
    s.require(api.app()['id'] == APP, 'Wrong Musia app')
    reservation = api.request('GET', '/v1/buildUploads/' + upload['buildUploadId'])['data']
    attrs = reservation['attributes']
    s.require(attrs['cfBundleVersion'] == manifest['build'] and attrs['cfBundleShortVersionString'] == manifest['version']
              and attrs['platform'] == manifest['platform'], 'Reservation identity mismatch')
    file = api.request('GET', '/v1/buildUploadFiles/' + upload['fileId'])['data']
    linked_files = api.rows('/v1/buildUploads/' + reservation['id'] + '/buildUploadFiles?limit=200')
    s.require(file['id'] in {row['id'] for row in linked_files}, 'Upload file belongs elsewhere')
    file_state = file['attributes']['assetDeliveryState']['state']
    builds = s.apple_platform_builds(api, APP, manifest['build'], manifest['platform'])
    outcome = dict(at=s.now(), platform=manifest['platform'], version=manifest['version'], build=manifest['build'],
                   upload_state=attrs['state']['state'], file_state=file_state, available=False)
    evidence = s.RUNTIME / 'apple-internal' / (manifest['platform'] + '-' + manifest['artifact']['sha256'])
    s.write_private(evidence / 'processing.json', dict(outcome=outcome, reservation=reservation, file=file, builds=builds))
    if len(builds) != 1 or builds[0]['attributes']['processingState'] != 'VALID':
        return dict(outcome, state='processing_or_reconciliation_required')
    build = builds[0]; build_id = build['id']
    linked_build = reservation.get('relationships', {}).get('build', {}).get('data')
    s.require(linked_build and linked_build.get('id') == build_id, 'Processed build not bound to this upload')
    owner = api.request('GET', '/v1/builds/' + build_id + '/app')['data']
    train = api.request('GET', '/v1/builds/' + build_id + '/preReleaseVersion')['data']['attributes']
    s.require(owner['id'] == APP and owner['attributes']['bundleId'] == s.BUNDLE
              and train['platform'] == manifest['platform'] and train['version'] == manifest['version']
              and not build['attributes'].get('expired'), 'Processed build identity mismatch')
    s.require(file_state == 'COMPLETE', 'Upload file not confirmed complete')
    checksums = file['attributes'].get('sourceFileChecksums', {})
    expected = hashlib.md5(Path(manifest['artifact']['path']).read_bytes()).hexdigest()
    s.require(checksums.get('file', {}).get('hash', '').lower() == expected
              and checksums.get('file', {}).get('algorithm') == 'MD5', 'Apple file checksum unconfirmed')
    groups = [g for g in api.rows('/v1/apps/' + APP + '/betaGroups?limit=200') if g['attributes']['name'] == 'Musia Internal']
    s.require(len(groups) == 1 and groups[0]['attributes'].get('isInternalGroup') is True
              and groups[0]['attributes'].get('hasAccessToAllBuilds') is False, 'Existing internal group unqualified')
    group = groups[0]
    tester = apple_owner_tester(api, APP, s.config()['self_tester_email'])
    members = api.rows('/v1/betaGroups/' + group['id'] + '/relationships/betaTesters?limit=200')
    s.require(tester['id'] in {t['id'] for t in members}, 'Existing owner not in group; no account change')
    relation = '/v1/betaGroups/' + group['id'] + '/relationships/builds'
    attached = build_id in {b['id'] for b in api.rows(relation + '?limit=200')}
    before = formal_attachments(api, APP)
    if confirm and not attached:
        with s.lock('apple-invite'):
            api.request('POST', relation, {'data': [{'type': 'builds', 'id': build_id}]},
                        operation='musia-internal-builds-' + build_id)
        attached = build_id in {b['id'] for b in api.rows(relation + '?limit=200')}
    internal = api.request('GET', '/v1/builds/' + build_id + '/buildBetaDetail')['data']['attributes']['internalBuildState']
    after = formal_attachments(api, APP)
    s.require(before == after, 'Formal binding changed; reconcile')
    available = attached and internal == 'IN_BETA_TESTING'
    outcome.update(state='available_to_internal_owner' if available else 'internal_availability_pending',
                   build_id=build_id, processing='VALID', in_internal_group=attached,
                   internal_state=internal, owner_membership_verified=True, available=available,
                   formal_attachments_preserved=True, email_delivery='not independently verified; no resend')
    s.write_private(evidence / 'delivery.json', dict(outcome=outcome, formal_before=before, formal_after=after))
    return outcome


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--confirm-attach', action='store_true')
    args = parser.parse_args()
    print(json.dumps(deliver(args.manifest, args.confirm_attach), indent=2))
