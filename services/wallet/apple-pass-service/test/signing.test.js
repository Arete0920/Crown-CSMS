import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { unzipSync } from 'fflate';
import { createPass } from '../server.js';

test('P12 signing preserves ticket fields, verifies CMS and rejects tampering/configuration failures', () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'crown-wallet-test-'));
  const file = name => path.join(directory, name);
  const openssl = args => execFileSync('openssl', args, { stdio: ['ignore', 'pipe', 'pipe'] });
  const tempPassDirectories = () => fs.readdirSync(os.tmpdir()).filter(name => name.startsWith('crown-pass-')).sort();
  try {
    openssl(['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
      '-subj', '/CN=Temporary Wallet Test CA', '-keyout', file('ca.key'), '-out', file('ca.pem')]);
    openssl(['req', '-new', '-newkey', 'rsa:2048', '-nodes',
      '-subj', '/CN=Temporary Pass/OU=TESTTEAM/UID=pass.test.crown',
      '-keyout', file('key.pem'), '-out', file('pass.csr')]);
    openssl(['x509', '-req', '-in', file('pass.csr'), '-CA', file('ca.pem'),
      '-CAkey', file('ca.key'), '-CAcreateserial', '-days', '1', '-out', file('cert.pem')]);
    openssl(['pkcs12', '-export', '-in', file('cert.pem'), '-inkey', file('key.pem'),
      '-out', file('signer.p12'), '-passout', 'pass:temporary-test-password']);
    const template = file('template');
    fs.mkdirSync(template);
    fs.copyFileSync(new URL('../template/pass.json', import.meta.url), path.join(template, 'pass.json'));
    const icon = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aP1sAAAAASUVORK5CYII=', 'base64');
    for (const name of ['icon.png', 'icon@2x.png']) fs.writeFileSync(path.join(template, name), icon);
    fs.mkdirSync(path.join(template, 'en.lproj'));
    fs.writeFileSync(path.join(template, 'en.lproj/pass.strings'), '"Event" = "Event";');
    const options = { template, certP12: fs.readFileSync(file('signer.p12')),
      certPass: 'temporary-test-password', wwdr: fs.readFileSync(file('ca.pem')),
      passTypeId: 'pass.test.crown', teamId: 'TESTTEAM', serial: 'ticket-123',
      eventName: 'Crown Celebration', purchaserEmail: 'test@example.invalid', seatLabel: 'A12', qrValue: 'qr-123' };
    const before = tempPassDirectories();
    const entries = unzipSync(createPass(options));
    const manifest = JSON.parse(Buffer.from(entries['manifest.json']).toString());
    for (const [name, hash] of Object.entries(manifest)) {
      assert.equal(createHash('sha1').update(entries[name]).digest('hex'), hash);
    }
    assert.ok(entries['en.lproj/pass.strings']);
    const pass = JSON.parse(Buffer.from(entries['pass.json']).toString());
    assert.equal(pass.serialNumber, options.serial);
    assert.equal(pass.barcodes[0].message, options.qrValue);
    assert.equal(pass.eventTicket.primaryFields[0].value, 'A12');
    fs.writeFileSync(file('signature'), entries.signature);
    fs.writeFileSync(file('manifest.json'), entries['manifest.json']);
    const verify = ['cms', '-verify', '-binary', '-inform', 'DER', '-in', file('signature'),
      '-content', file('manifest.json'), '-CAfile', file('ca.pem'), '-purpose', 'any'];
    assert.deepEqual(openssl(verify), Buffer.from(entries['manifest.json']));
    fs.appendFileSync(file('manifest.json'), 'tampered');
    assert.throws(() => openssl(verify));
    assert.throws(() => createPass({ ...options, teamId: 'OTHERTEAM' }), /Pass signing failed/);
    assert.throws(() => createPass({ ...options, certPass: 'wrong-password' }), /Pass signing failed/);
    fs.unlinkSync(path.join(template, 'icon.png'));
    assert.throws(() => createPass(options), /icons are required/);
    assert.deepEqual(tempPassDirectories(), before, 'temporary signing material is removed');
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});
