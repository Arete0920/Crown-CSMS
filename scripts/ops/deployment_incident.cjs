'use strict';

// Job evidence is attempt-specific. Missing or ambiguous evidence is never "no".
function productionMutation(jobs) {
  const names = ['production-migration', 'build-and-deploy'];
  if (!Array.isArray(jobs)) return 'unknown';
  const rows = names.map(name => jobs.filter(job => job.name === name));
  if (rows.some(matches => matches.length !== 1)) return 'unknown';
  if (rows.every(([job]) => job.status === 'completed' && job.conclusion === 'skipped'
      && (!job.steps || job.steps.length === 0))) return 'no';
  return 'possible';
}

function incidentReport(env, upstream, timestamp) {
  const mutation = ['no', 'possible'].includes(env.PRODUCTION_MUTATION)
    ? env.PRODUCTION_MUTATION : 'unknown';
  const health = ['healthy', 'unhealthy'].includes(env.HEALTH_STATUS)
    ? env.HEALTH_STATUS : 'unknown';
  const needed = ['true', 'false'].includes(env.ROLLBACK_NEEDED)
    ? env.ROLLBACK_NEEDED : 'unknown';
  const validSha = value => /^[0-9a-f]{40}$/.test(value || '');
  const verified = mutation === 'possible' && needed === 'true'
    && env.RESTORE_OUTCOME === 'success' && env.VERIFY_OUTCOME === 'success'
    && validSha(env.ROLLBACK_SHA) && env.VERIFIED_SHA === env.ROLLBACK_SHA
    && Boolean(env.RESTORED_IMAGE);
  let title, labels, summary;
  if (mutation === 'no') {
    title = '[ADVISORY] Production release blocked before mutation';
    labels = health === 'unhealthy' ? ['production-alert', 'incident'] : ['production-advisory'];
    summary = [
      'Both production-migration and build-and-deploy were skipped in the failed upstream attempt.',
      'This attempt did not migrate or deploy production; rollback for this candidate is not applicable.',
      `Current runtime health observation: ${health}. No outage causation or recovery is established.`
    ];
  } else if (verified) {
    title = '[INCIDENT] Immutable rollback verified';
    labels = ['production-alert', 'incident', 'rollback-executed'];
    summary = ['CROWN restored an immutable image and verified its exact build SHA and database health.',
      'The failed workflow alone does not establish the cause of the earlier health observation.'];
  } else if (health === 'healthy') {
    title = '[ADVISORY] Production workflow failed; runtime observed healthy';
    labels = ['production-advisory'];
    summary = ['The health probe observed a healthy runtime. This is not evidence of production recovery.',
      'Production mutation and rollback evidence must be evaluated separately.'];
  } else if (health === 'unhealthy') {
    title = '[INCIDENT] Runtime health check failed; recovery not verified';
    labels = ['production-alert', 'incident'];
    if (needed === 'true' && env.RESTORE_OUTCOME === 'failure') labels.push('rollback-failed');
    summary = ['The live probe failed its health criteria; deployment causation is not established.',
      'Verified recovery is absent. Manual incident control is required.'];
  } else {
    title = '[INCIDENT] Production status unknown; verification blocked';
    labels = ['production-alert', 'incident'];
    summary = ['Live health was not established. An outage, failed rollback, and recovery are not proven.',
      'Resolve the evidence or authentication blocker before a production decision.'];
  }
  return {
    title: `${title} (${timestamp})`, labels,
    body: [
      `Upstream workflow: ${upstream?.name || '(unknown)'}`,
      `Upstream run: ${upstream?.html_url || '(unknown)'}`,
      `Upstream attempt: ${upstream?.run_attempt || '(unknown)'}`,
      `Failed candidate SHA: ${upstream?.head_sha || '(unknown)'}`,
      '', '## Summary', ...summary, '', '## Evidence',
      `- Production mutation: ${mutation}`,
      `- Runtime health observation: ${health}`,
      `- Observed live SHA: ${validSha(env.PRE_ROLLBACK_SHA) ? env.PRE_ROLLBACK_SHA : '(not verified)'}`,
      `- Rollback required: ${mutation === 'no' ? 'not applicable' : needed}`,
      `- Restore step outcome: ${env.RESTORE_OUTCOME || '(not run or unknown)'}`,
      `- Verification step outcome: ${env.VERIFY_OUTCOME || '(not run or unknown)'}`,
      `- Last-known-good source run: ${env.SOURCE_RUN_URL || '(not applicable or unresolved)'}`,
      `- Last-known-good source run ID: ${env.SOURCE_RUN_ID || '(not applicable or unresolved)'}`,
      `- Immutable rollback SHA: ${env.ROLLBACK_SHA || '(not applicable or unresolved)'}`,
      `- Restored image: ${env.RESTORED_IMAGE || '(not applicable or unresolved)'}`,
      `- Verified recovery SHA: ${verified ? env.VERIFIED_SHA : '(not verified)'}`,
      '', '## Required Follow-up',
      '- Review the original failure and release authority evidence before another production attempt.',
      '- Missing evidence must remain unknown; do not infer outage causation from workflow failure.',
      '- Do not report recovery without successful restoration and exact runtime identity verification.'
    ].join('\n')
  };
}

module.exports = { productionMutation, incidentReport };
