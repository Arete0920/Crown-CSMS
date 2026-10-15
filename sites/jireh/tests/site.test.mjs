import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync,existsSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
const root=new URL('../',import.meta.url);
const read=p=>readFileSync(new URL(p,root),'utf8');
const html=read('index.html');
const css=read('../shared/product-theme.css');
const security=JSON.parse(read('staticwebapp.config.json'));
test('full Jireh product family and accurate release claims',()=>{
for(const word of ['JIREH FINANCIAL AID','Provision with Purpose.','Stewardship with Wisdom.','Jireh SGO','pilot development','CROWN Jireh','Request a Jireh demonstration','Request an SGO pilot discussion','not a scholarship-granting organization','no instant reservation','Privacy','Terms']){
 assert.ok(html.toLowerCase().includes(word.toLowerCase()),'missing '+word);
}
assert.equal((html.match(/<h1\b/g)||[]).length,1);
assert.ok(!/<form\b/i.test(html),'Unverified form must not be presented as live demo booking');
assert.ok(!/<script\b/i.test(html),'No third-party scripting is permitted');
assert.ok(/not a live application screenshot/i.test(html),'Hero illustration must not imply deployed software');
});
test('hero calls to action and accessible navigation',()=>{
const hero=html.slice(html.indexOf('<section class="hero"'),html.indexOf('<section id="school-aid"'));
assert.ok(/Request a Jireh demonstration/.test(hero),'primary conversion action must be above fold');
assert.ok(/Explore school financial aid/.test(hero));
assert.ok(/<details class="mobile-menu">/.test(html),'mobile navigation cannot disappear');
assert.ok(/class="skip"/.test(html));
for(const anchor of ['school-aid','workflow','sgo','demo']) assert.ok(html.includes('id="'+anchor+'"'));
});
test('one shared brand palette and responsive keyboard-safe layout',()=>{
for(const token of ['--brand-navy','#173746','--brand-teal','#1c6064','--brand-gold','#d39c49','--brand-cream','#fcf8f0'])assert.ok(css.includes(token),'missing palette '+token);
assert.ok(css.includes('prefers-reduced-motion'));
assert.ok(css.includes('focus-visible'));
assert.ok(css.includes('max-width:700px'));
});
test('secure, non-indexed staging configuration',()=>{
assert.ok(html.includes('noindex,nofollow'));
assert.ok(read('robots.txt').includes('Disallow: /'));
assert.equal(security.globalHeaders['X-Frame-Options'],'DENY');
assert.ok(security.globalHeaders['Content-Security-Policy'].includes("default-src 'none'"));
});
test('source files assemble into deployable static output',()=>{
execFileSync(process.execPath,[new URL('../build.mjs',import.meta.url).pathname],{stdio:'pipe'});
for(const file of ['index.html','styles.css','robots.txt','staticwebapp.config.json'])assert.ok(existsSync(new URL('../dist/'+file,import.meta.url)));
assert.ok(read('dist/styles.css').includes('--brand-navy:#173746'));
});
