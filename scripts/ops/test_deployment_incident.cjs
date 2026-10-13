'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { productionMutation, incidentReport } = require('./deployment_incident.cjs');
const sha = 'a'.repeat(40);
const skipped = name => ({name, status: 'completed', conclusion: 'skipped', steps: null});
const jobs = [skipped('production-migration'), skipped('build-and-deploy')];
const report = env => incidentReport(env, {run_attempt: 1}, 'test');

test('preflight with both mutation jobs skipped cannot require rollback', () => {
  assert.equal(productionMutation(jobs), 'no');
  for (const health of ['healthy', 'unhealthy', '', 'unknown']) {
    const row = report({PRODUCTION_MUTATION: 'no', HEALTH_STATUS: health});
    assert.match(row.body, /Rollback required: not applicable/);
    assert.doesNotMatch(row.body, /left the runtime unhealthy/);
    assert.ok(!row.labels.includes('rollback-failed'));
    if (health === 'unhealthy') assert.ok(row.labels.includes('incident'));
  }
});
test('missing, duplicate, incomplete, or contradictory jobs never establish no mutation', () => {
  for (const rows of [undefined, [], jobs.slice(0, 1), [...jobs, jobs[0]]]) {
    assert.equal(productionMutation(rows), 'unknown');
  }
  for (const change of [{conclusion: 'failure'}, {status: 'in_progress'},
    {steps: [{conclusion: 'success'}]}]) {
    assert.equal(productionMutation([{...jobs[0], ...change}, jobs[1]]), 'possible');
  }
});
test('missing health/login evidence cannot become false rollback or proven outage', () => {
  const row = report({});
  assert.match(row.title, /status unknown/);
  assert.match(row.body, /Rollback required: unknown/);
  assert.match(row.body, /An outage, failed rollback, and recovery are not proven/);
  assert.ok(!row.labels.includes('rollback-failed'));
});
test('healthy observation is not recovery or historical continuity', () => {
  const row = report({PRODUCTION_MUTATION: 'possible', HEALTH_STATUS: 'healthy', ROLLBACK_NEEDED: 'false'});
  assert.match(row.title, /observed healthy/);
  assert.match(row.body, /not evidence of production recovery/);
  assert.doesNotMatch(row.body, /remained healthy/);
});
test('verified recovery requires successful restore/verify and exact matching full SHA', () => {
  const env = {PRODUCTION_MUTATION: 'possible', HEALTH_STATUS: 'unhealthy', ROLLBACK_NEEDED: 'true',
    RESTORE_OUTCOME: 'success', VERIFY_OUTCOME: 'success', ROLLBACK_SHA: sha,
    VERIFIED_SHA: sha, RESTORED_IMAGE: `registry/image:${sha}`};
  assert.ok(report(env).labels.includes('rollback-executed'));
  for (const change of [{VERIFIED_SHA: 'b'.repeat(40)}, {VERIFIED_SHA: 'abc'},
    {RESTORE_OUTCOME: 'failure'}, {VERIFY_OUTCOME: 'skipped'}, {RESTORED_IMAGE: ''},
    {PRODUCTION_MUTATION: 'unknown'}, {ROLLBACK_NEEDED: ''}]) {
    const row = report({...env, ...change});
    assert.ok(!row.labels.includes('rollback-executed'));
    assert.match(row.body, /Verified recovery SHA: \(not verified\)/);
  }
});
test('rollback-failed label requires an actual failed restore', () => {
  const env = {PRODUCTION_MUTATION: 'possible', HEALTH_STATUS: 'unhealthy', ROLLBACK_NEEDED: 'true'};
  assert.ok(!report(env).labels.includes('rollback-failed'));
  assert.ok(report({...env, RESTORE_OUTCOME: 'failure'}).labels.includes('rollback-failed'));
});
