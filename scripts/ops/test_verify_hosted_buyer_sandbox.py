"""Offline security and release-claim checks for the read-only hosted buyer precheck."""

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import verify_dev_owner_runtime as existing
import verify_hosted_buyer_sandbox as buyer

SHA = 'a' * 40
INVITE = 'sbx_inv_' + 'A' * 24


def catalog():
    return {
        'schools': [{'key': 'heritage-core', 'track': 'school'}],
        'tracks': [{'key': 'school'}],
        'personas': [{'key': role} for role in sorted(buyer.EXPECTED_ROLES)],
    }


class FakeRead:
    def __init__(self, *, cat=None, page=200, cors=204, hdr=None, invite=None, invite_status=200, request_id=INVITE):
        self.calls = []
        self.request_id = request_id
        self.cat = catalog() if cat is None else cat
        self.page = page
        self.cors = cors
        self.headers = hdr if hdr is not None else {
            'Access-Control-Allow-Origin': existing.PREVIEW,
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Access-Control-Allow-Headers': 'content-type,authorization',
        }
        self.invite = invite if invite is not None else {
            'invite_id': request_id, 'usable': True, 'track': 'school',
            'allowed_roles': ['school_admin', 'parent'],
            'allowed_seed_packs': ['heritage-core'], 'revoked_at': None,
        }
        self.invite_status = invite_status

    def __call__(self, opener, url, *, method='GET', headers=None, read_json=False):
        self.calls.append((url, method, headers, read_json))
        self._assert_no_auth(headers)
        if url == existing.API + '/api/v1/sandbox/catalog/':
            return 200, {}, self.cat
        if url == existing.PREVIEW + '/sandbox':
            return self.page, {}, None
        if url == existing.API + '/api/v1/sandbox/session/':
            assert method == 'OPTIONS'
            assert headers == {
                'Origin': existing.PREVIEW,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'content-type',
            }
            return self.cors, self.headers, None
        if url == existing.API + '/api/v1/sandbox/invites/' + self.request_id + '/':
            return self.invite_status, {}, self.invite
        raise AssertionError('Unexpected URL ' + url)

    def _assert_no_auth(self, headers):
        assert not any('authorization' == k.lower() or 'cookie' == k.lower()
                       for k in (headers or {}))


def run(fake, *, sha=SHA, invite=None, baseline='PASS'):
    with patch.object(existing, '_open_request', fake):
        return buyer.probe(
            sha, invite_id=invite, opener=object(),
            identity_probe=lambda expected, *, opener: {'precheck': baseline},
        )


class HostedBuyerSecurityTests(unittest.TestCase):
    def test_all_public_checks_still_cannot_certify_link_or_modules(self):
        fake = FakeRead()
        report = run(fake)
        self.assertEqual(report['public_precheck'], 'PASS')
        self.assertEqual(report['invite_precheck'], 'BLOCKED')
        self.assertFalse(report['release_certified'])
        self.assertEqual(report['email_full_demo_link'], 'NO_GO')
        self.assertEqual(set(report['signed_5_module_write_get_reload_and_negative_tests']), set(buyer.FIVE_MODULES))
        self.assertTrue(all(x == 'NOT_TESTED' for x in report['signed_5_module_write_get_reload_and_negative_tests'].values()))
        self.assertEqual([x[1] for x in fake.calls], ['GET', 'GET', 'OPTIONS'])
        self.assertNotIn('password', json.dumps(report).lower())

    def test_valid_existing_invite_is_only_metadata_acceptance(self):
        fake = FakeRead()
        report = run(fake, invite=INVITE)
        self.assertEqual(report['invite_precheck'], 'PASS')
        self.assertEqual(report['public_precheck'], 'PASS')
        self.assertFalse(report['release_certified'])
        self.assertEqual(report['email_full_demo_link'], 'NO_GO')
        self.assertEqual(len(fake.calls), 4)
        self.assertNotIn(INVITE, json.dumps(report))

    def test_valid_shorter_legacy_invite_id_is_accepted_without_release_claim(self):
        # make_invite_id removes URL-safe base64 punctuation after token creation;
        # therefore a valid stored ID can have fewer than 24 suffix characters.
        short = 'sbx_inv_' + 'B' * 22
        report = run(FakeRead(request_id=short), invite=short)
        self.assertEqual(report['invite_precheck'], 'PASS')
        self.assertEqual(report['email_full_demo_link'], 'NO_GO')
        self.assertNotIn(short, json.dumps(report))

    def test_invalid_invite_rejected_before_any_requests(self):
        for value in ('', 'sbx_inv', 'a' * 80, '../escape', INVITE + '\n', INVITE + '?secret=x'):
            with self.subTest(value=value):
                fake = FakeRead()
                with self.assertRaises(ValueError):
                    run(fake, invite=value)
                self.assertEqual(fake.calls, [])

    def test_bad_sha_rejected_before_any_requests(self):
        for value in ('main', 'A' * 40, 'a' * 39, SHA + '\n'):
            with self.subTest(value=value):
                fake = FakeRead()
                with self.assertRaises(ValueError):
                    run(fake, sha=value)
                self.assertEqual(fake.calls, [])

    def test_existing_identity_drift_never_passes_public_precheck(self):
        report = run(FakeRead(), baseline='BLOCKED')
        self.assertEqual(report['public_precheck'], 'BLOCKED')

    def test_foreign_school_fails_closed(self):
        bad = catalog()
        bad['schools'].append({'key': 'some-other-school', 'track': 'school'})
        report = run(FakeRead(cat=bad))
        self.assertEqual(report['public_checks']['public_sandbox_catalog_heritage_only'], 'BLOCKED')

    def test_missing_expected_persona_and_extra_persona_both_fail(self):
        for mutation in ('missing', 'extra'):
            cat = catalog()
            if mutation == 'missing':
                cat['personas'].pop()
            else:
                cat['personas'].append({'key': 'school_superuser'})
            self.assertEqual(run(FakeRead(cat=cat))['public_precheck'], 'BLOCKED')

    def test_frontend_route_not_http_200_fails(self):
        for code in (301, 302, 401, 403, 404, 503, None):
            self.assertEqual(run(FakeRead(page=code))['public_precheck'], 'BLOCKED')

    def test_cors_cannot_wildcard_or_omit_credential_header(self):
        for hdr in (
            {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Credentials': 'true',
             'Access-Control-Allow-Methods': 'POST', 'Access-Control-Allow-Headers': 'content-type'},
            {'Access-Control-Allow-Origin': existing.PREVIEW,
             'Access-Control-Allow-Methods': 'POST', 'Access-Control-Allow-Headers': 'content-type'},
            {'Access-Control-Allow-Origin': existing.PREVIEW, 'Access-Control-Allow-Credentials': 'true',
             'Access-Control-Allow-Methods': 'POST', 'Access-Control-Allow-Headers': 'authorization'},
            {'Access-Control-Allow-Origin': existing.PREVIEW, 'Access-Control-Allow-Credentials': 'true',
             'Access-Control-Allow-Methods': 'GET', 'Access-Control-Allow-Headers': 'content-type'},
        ):
            with self.subTest(hdr=hdr):
                self.assertEqual(run(FakeRead(hdr=hdr))['public_precheck'], 'BLOCKED')

    def test_cors_rejected_for_non_200_non_204(self):
        for code in (301, 302, 403, 404, 500):
            self.assertEqual(run(FakeRead(cors=code))['public_precheck'], 'BLOCKED')

    def test_invite_wrong_scope_revoked_or_expired_fails(self):
        variants = (
            {'usable': False}, {'track': 'other'},
            {'allowed_roles': ['unknown_privileged_role']}, {'allowed_roles': []},
            {'allowed_seed_packs': ['another-school']},
            {'allowed_seed_packs': ['heritage-core', 'another-school']},
            {'revoked_at': '2026-01-01T00:00:00+00:00'}, {'invite_id': 'another'},
        )
        for delta in variants:
            with self.subTest(delta=delta):
                payload = dict(FakeRead().invite, **delta)
                self.assertEqual(run(FakeRead(invite=payload), invite=INVITE)['invite_precheck'], 'BLOCKED')

    def test_explicit_hosted_daycare_invite_is_only_metadata_evidence(self):
        fake = FakeRead()
        fake.invite["allowed_roles"] = ["daycare_director"]
        report = run(fake, invite=INVITE)
        self.assertEqual(report["invite_precheck"], "PASS")
        self.assertFalse(report["release_certified"])
        self.assertEqual(report["email_full_demo_link"], "NO_GO")

    def test_error_or_404_invite_never_exposes_identifier(self):
        fake = FakeRead(invite_status=404)
        report = run(fake, invite=INVITE)
        self.assertEqual(report['invite_precheck'], 'BLOCKED')
        self.assertNotIn(INVITE, json.dumps(report))

    def test_cli_never_outputs_invite_and_never_claims_release(self):
        out = io.StringIO()
        with patch('sys.stdin', io.StringIO(INVITE + '\n')):
            with patch.object(buyer, 'probe', return_value={
                'public_precheck': 'PASS', 'invite_precheck': 'PASS',
                'release_certified': False, 'email_full_demo_link': 'NO_GO',
            }):
                with redirect_stdout(out):
                    code = buyer.main(['--expected-sha', SHA, '--invite-stdin'])
        self.assertEqual(code, 0)  # Read-only precheck exit, never buyer release.
        self.assertNotIn(INVITE, out.getvalue())
        self.assertEqual(json.loads(out.getvalue())['email_full_demo_link'], 'NO_GO')

    def test_headers_compare_case_insensitively_without_origin_wildcard(self):
        self.assertTrue(buyer._cors_allows(FakeRead().headers, origin=existing.PREVIEW,
                                            method='post', required_headers={'content-type'}))
        self.assertFalse(buyer._cors_allows(FakeRead().headers, origin='https://other.invalid',
                                             method='POST', required_headers={'content-type'}))


if __name__ == '__main__':
    unittest.main()
