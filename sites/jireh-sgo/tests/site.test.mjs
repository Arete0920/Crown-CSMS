import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const base = new URL('../', import.meta.url);
const read = p => readFileSync(new URL(p,base),'utf8');
const html=read('index.html');
const css=read('styles.css');
const config=JSON.parse(read('staticwebapp.config.json'));
for(const text of ['Jireh SGO','IN PILOT DEVELOPMENT','design-partner discussion','No-cost exploratory conversation','Not certified for operational use','not an automated booking','not a scholarship-granting organization','Family applies','Both reconcile','Privacy','Terms']){
  assert.ok(html.toLowerCase().includes(text.toLowerCase()),'Required release disclosure/content missing: '+text);
}
for(const fragment of ['#responsibilities','#workflow','#status','#partners']) assert.ok(html.includes('id="'+fragment.slice(1)+'"'));
assert.ok(!/<form\b/i.test(html),'A deceptive or unproven lead form must not be shipped');
assert.ok(!/<script\b/i.test(html),'Static pilot should not execute third-party scripts');
assert.ok(html.includes('noindex,nofollow'),'Pilot staging must not index');
assert.ok(html.includes('/resources/jireh-sgo-overview.pdf'),'Approved overview still linked');
assert.ok(html.includes('areteadvisorygroup.com/contact?topic='),'Existing inquiry route retained');
assert.ok(!/\b(fully live|production ready|certified compliant|instant booking)\b/i.test(html),'Unverified claim');
assert.ok(css.includes('prefers-reduced-motion'));
assert.equal(config.globalHeaders['X-Frame-Options'],'DENY');
assert.ok(config.globalHeaders['Content-Security-Policy'].includes("default-src 'none'"));
assert.ok(read('robots.txt').includes('Disallow: /'));
console.log('Jireh SGO staging content and safety checks: PASS');
