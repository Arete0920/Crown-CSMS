import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const baseUrl = process.env.CROWN_BASE_URL || 'http://localhost:3000';
const outDir = process.env.CROWN_OUT || './audit-out';
mkdirSync(outDir, { recursive: true });
mkdirSync(join(outDir, 'shots'), { recursive: true });

// Group A: legacy short routes (Group 1 + Group 2 — what I've been working on)
const LEGACY = [
  '/admin', '/teacher', '/parent', '/student', '/admissions', '/finance', '/communications',
  '/board', '/it', '/marketing', '/spiritual-life', '/office', '/health', '/counseling',
  '/food', '/athletics', '/registrar',
];

// Group B: canonical dashboardRegistry paths
const CANONICAL = [
  '/admissions-dashboard', '/attendance-dashboard', '/billing-dashboard', '/financial-aid-dashboard',
  '/registrar-dashboard', '/scheduling-dashboard', '/gradebook-dashboard', '/student-care-dashboard',
  '/activities-dashboard', '/communications-dashboard',
  '/school-admin-dashboard', '/school-board-dashboard', '/master-control-dashboard', '/advancement-dashboard',
  '/hr-dashboard', '/facilities-dashboard', '/health-office-dashboard', '/transportation-dashboard',
  '/food-service-dashboard', '/it-support-dashboard',
  '/fine-arts-dashboard', '/athletics-director-dashboard', '/library-media-dashboard',
  '/extended-care-dashboard', '/safety-security-dashboard', '/curriculum-pd-dashboard',
  '/chaplain-dashboard', '/advancement-operations-dashboard', '/volunteer-management-dashboard',
  '/portrait-service-dashboard', '/alumni-relations-dashboard', '/network-benchmarking-dashboard',
  '/implementation-success-dashboard', '/data-migration-dashboard', '/integrations-automation-dashboard',
  '/compliance-audit-dashboard', '/revenue-operations-dashboard', '/release-reliability-dashboard',
  '/dashboard-certification-center',
];

const ROUTES = [
  ...LEGACY.map(p => ({ group: 'A-legacy', path: p })),
  ...CANONICAL.map(p => ({ group: 'B-canonical', path: p })),
];

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const results = [];

for (const { group, path } of ROUTES) {
  const page = await ctx.newPage();
  const consoleErrs = [];
  const pageErrs = [];
  page.on('pageerror', e => pageErrs.push(String(e.message).slice(0, 200)));
  page.on('console', m => { if (m.type() === 'error') consoleErrs.push(m.text().slice(0, 200)); });

  let httpStatus = 0;
  try {
    const resp = await page.goto(baseUrl + path, { waitUntil: 'networkidle', timeout: 30000 });
    httpStatus = resp ? resp.status() : 0;
  } catch (e) {
    pageErrs.push('goto:' + e.message.slice(0, 150));
  }
  await page.waitForTimeout(700);

  const probe = await page.evaluate(() => {
    const text = document.body?.innerText || '';
    const h1 = document.querySelector('h1')?.innerText?.slice(0, 120) || '';
    return {
      h1,
      // Gold-standard markers
      hasGreeting: /Good morning,/i.test(text),
      hasHCA: /Heritage Christian Academy/i.test(text),
      hasLaunchPreview: /CROWN Launch Preview/i.test(text),
      hasSystemHealth: /System health/i.test(text),
      // Old/broken markers
      hasOfflineFallback: /Offline\/Fallback/i.test(text),
      hasNavUnavail: /Navigation service unavailable/i.test(text),
      hasNotFound: /Page not found|404/i.test(text),
      hasNotAuthorized: /Not Authorized|Forbidden/i.test(text),
      hasPlaceholder: /Coming soon|placeholder|Under construction/i.test(text),
      // Optional: count metric cards / module cards if standard
      bodyChars: text.length,
    };
  });

  // Internal hrefs (relative or same-origin) for link inventory
  const links = await page.evaluate((origin) => {
    const set = new Set();
    document.querySelectorAll('a[href]').forEach(a => {
      const href = a.getAttribute('href') || '';
      if (!href) return;
      if (href.startsWith('/')) set.add(href.split('#')[0]);
      else if (href.startsWith(origin)) set.add(href.slice(origin.length).split('#')[0]);
    });
    return [...set];
  }, baseUrl);

  // Verdict
  let verdict = 'UNKNOWN';
  if (probe.hasNotFound) verdict = 'NOT_FOUND';
  else if (probe.hasNotAuthorized) verdict = 'AUTH_BLOCKED';
  else if (probe.hasOfflineFallback || probe.hasNavUnavail) verdict = 'OLD_CHROME';
  else if (probe.hasGreeting && probe.hasHCA && probe.hasLaunchPreview && probe.hasSystemHealth) verdict = 'GOLD';
  else if (probe.hasPlaceholder) verdict = 'PLACEHOLDER';
  else verdict = 'OTHER';

  const slug = path.replace(/[^a-z0-9]/gi, '_').replace(/^_/, '') || 'root';
  const shotPath = join(outDir, 'shots', `${slug}.png`);
  await page.screenshot({ path: shotPath, fullPage: false });

  results.push({
    group, path, httpStatus, verdict,
    h1: probe.h1,
    g: probe.hasGreeting, hca: probe.hasHCA, lp: probe.hasLaunchPreview, sh: probe.hasSystemHealth,
    off: probe.hasOfflineFallback, nav: probe.hasNavUnavail, nf: probe.hasNotFound, nz: probe.hasNotAuthorized, pl: probe.hasPlaceholder,
    consoleErrs: consoleErrs.length, pageErrs: pageErrs.length,
    consoleErrSample: consoleErrs.slice(0, 3),
    pageErrSample: pageErrs.slice(0, 3),
    internalLinks: links,
  });

  console.log(`${verdict.padEnd(13)} ${group.padEnd(12)} ${path.padEnd(45)} h1="${probe.h1.slice(0,50)}" ce=${consoleErrs.length} pe=${pageErrs.length}`);
  await page.close();
}

// Build link → set-of-source-pages map and verify each unique link target also returns a real route
const linkSet = new Set();
for (const r of results) for (const l of r.internalLinks) linkSet.add(l);

console.log(`\nDiscovered ${linkSet.size} unique internal href targets across ${results.length} pages.`);

const linkChecks = [];
for (const link of [...linkSet].sort()) {
  const page = await ctx.newPage();
  let status = 0;
  try {
    const resp = await page.goto(baseUrl + link, { waitUntil: 'domcontentloaded', timeout: 15000 });
    status = resp ? resp.status() : 0;
  } catch (e) { /* ignore */ }
  await page.waitForTimeout(300);
  const probe = await page.evaluate(() => ({
    h1: document.querySelector('h1')?.innerText?.slice(0, 80) || '',
    text: document.body?.innerText?.slice(0, 600) || '',
  }));
  const isNotFound = /Page not found|404|Looking for something|We couldn't find/i.test(probe.text);
  linkChecks.push({ link, status, h1: probe.h1, notFound: isNotFound });
  await page.close();
}

writeFileSync(join(outDir, 'audit.json'), JSON.stringify({ results, linkChecks }, null, 2));

// Build markdown summary
const lines = [];
lines.push(`# Crown Dashboards — Comprehensive Local Audit`);
lines.push(`Base URL: ${baseUrl}`);
lines.push(`Generated: ${new Date().toISOString()}`);
lines.push(``);
const counts = results.reduce((a, r) => { a[r.verdict] = (a[r.verdict]||0)+1; return a; }, {});
lines.push(`## Verdict tally`);
for (const [v, n] of Object.entries(counts)) lines.push(`- ${v}: ${n}`);
lines.push(``);
lines.push(`## Per-route results`);
lines.push(`| Group | Route | Verdict | h1 | Greeting | HCA | LaunchPrev | SysHealth | Offline | NavFail | ConsoleErr | PageErr |`);
lines.push(`|---|---|---|---|---|---|---|---|---|---|---|---|`);
for (const r of results) {
  lines.push(`| ${r.group} | \`${r.path}\` | **${r.verdict}** | ${r.h1.replace(/\|/g,'')} | ${r.g?'✓':'✗'} | ${r.hca?'✓':'✗'} | ${r.lp?'✓':'✗'} | ${r.sh?'✓':'✗'} | ${r.off?'⚠':''} | ${r.nav?'⚠':''} | ${r.consoleErrs} | ${r.pageErrs} |`);
}
lines.push(``);
lines.push(`## Internal link health (${linkChecks.length} unique hrefs)`);
const broken = linkChecks.filter(l => l.status !== 200 || l.notFound);
lines.push(`Broken or 404: **${broken.length}**`);
if (broken.length) {
  lines.push(`| Link | HTTP | NotFound | h1 |`);
  lines.push(`|---|---|---|---|`);
  for (const b of broken) lines.push(`| \`${b.link}\` | ${b.status} | ${b.notFound?'YES':''} | ${b.h1} |`);
}
writeFileSync(join(outDir, 'SUMMARY.md'), lines.join('\n'));

const goldCount = results.filter(r => r.verdict === 'GOLD').length;
console.log(`\n=== TOTAL ===`);
console.log(`GOLD: ${goldCount}/${results.length}`);
for (const [v, n] of Object.entries(counts)) console.log(`${v}: ${n}`);
console.log(`Broken links: ${broken.length}/${linkChecks.length}`);
console.log(`\nReport: ${outDir}\\SUMMARY.md`);
console.log(`JSON:   ${outDir}\\audit.json`);

await browser.close();
process.exit(0);
