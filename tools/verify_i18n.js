// Page-level language check, run through the real generator.
//
//   node scripts/verify_i18n.js               # check index.html as committed
//   node scripts/verify_i18n.js /tmp/gen.html # check a generated build first
//
// Two things must hold, per the standing rule that a build with no Vietnamese
// output is a broken build: the generator's self-test must pass (it covers the
// three ways a dictionary can go green while useless — an escaped &amp; key, a
// selector matching script code, a long run served by one of its own words), and
// the Vietnamese render must exist and differ from the English render. Coverage is
// reported, never asserted per key: a key that matches nothing is reported and
// stays a MISS, it cannot make the build pass or fail.
const {execFileSync, execSync} = require('child_process');
const fs = require('fs');
const path = require('path');
const target = process.argv[2] || path.join(__dirname, '..', 'index.html');
const gen = path.join(__dirname, "build_i18n.py");
let failures = 0;
const fail = (m) => {failures++; console.log('FAIL: ' + m);};

try {
  const out = execFileSync('python3', [gen, '--self-test'], {encoding: 'utf8'});
  if (/FAIL/.test(out)) fail('generator self-test failed\n' + out);
} catch (e) {
  fail('generator self-test did not run: ' + (e.stdout || e.message).toString().trim().split('\n').slice(0, 4).join('\n'));
}

const html = fs.readFileSync(target, 'utf8');
// Order-agnostic: a unit may hold (en, vi) or (vi, en). Assuming one order leaves
// the other language's text in the "Vietnamese" render, and every check below
// then reads English that no reader is actually shown.
const UNIT = /<span class="i18n">((?:\s*<span lang="[a-z]{2}">[^<]*<\/span>\s*)+)<\/span>/g;
const render = (lang) => html
  .replace(UNIT, (m, body) => {
    const halves = [...body.matchAll(/<span lang="([a-z]{2})">([^<]*)<\/span>/g)]
      .map((h) => ({lang: h[1], text: h[2]}));
    const want = halves.filter((h) => h.lang === lang).map((h) => h.text).join(' ');
    return want || halves.map((h) => h.text).join(' ');   // no rendering = English shown
  })
  .replace(/<script[\s\S]*?<\/script>/g, '')
  .replace(/<style[\s\S]*?<\/style>/g, '')
  .replace(/<[^>]*>/g, ' ');
const en = render('en');
const vi = render('vi');

// A unit with only an English half is what the dictionary used to pass silently.
const lone = html.match(/<span class="i18n">\s*<span lang="en">([^<]{4,})<\/span>\s*<\/span>/g) || [];
if (lone.length) fail(lone.length + ' language units have English only: ' +
  lone.map((s) => s.replace(/<[^>]*>/g, '').trim()).slice(0, 6).join(' | '));

if (vi === en) fail('Vietnamese render is identical to English — nothing was translated');
// Raw & in Vietnamese: legal copy like "SOC 2 & ISO 27001" ships as a bare
// ampersand, which a browser reads as the start of an entity. The generator
// escapes on the way in, so this fails only when a hand edit reintroduces it.
const rawAmp = html.match(/lang="vi">[^<]*&(?!(amp|lt|gt|quot|#39|nbsp);)/g) || [];
if (rawAmp.length) fail(rawAmp.length + ' Vietnamese strings contain a raw & — escape it: ' +
  rawAmp.slice(0, 3).map((s) => s.slice(-40)).join(' | '));
const viMarks = (vi.match(/[ơưăêôđạảãáàẻẽéẹêểễệỉĩọỏóòợơụủùỷ]/g) || []).length;
if (viMarks < 200) fail('only ' + viMarks + ' Vietnamese marks in the Vietnamese render');
// A run the dictionary could have translated but did not: the key exists and its
// English still shows while the Vietnamese does not. That is the "Skip to main
// content" shape — the page looked bilingual and one label was never translated.
const dict = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'i18n', 'pairs.json'), 'utf8'));
const pairs = Object.entries({...dict.exact, ...dict.frag});
const skipped = pairs.filter(([en2, vi2]) => en2.length > 3 && /[A-Za-z][a-z]{3}/.test(en2) &&
  vi.includes(en2) && !vi.includes(vi2)).map(([en2]) => en2);
if (skipped.length) fail('a pair exists but Vietnamese still shows its English: ' +
  skipped.slice(0, 5).join(' | '));
console.log('coverage: ' + viMarks + ' Vietnamese marks in the Vietnamese render, ' +
  (html.match(/class="i18n"/g) || []).length + ' bilingual units, ' + lone.length + ' English-only');
console.log(failures ? failures + ' failures' : 'ok: generator self-test, both languages present, renders differ');
process.exit(failures ? 1 : 0);
