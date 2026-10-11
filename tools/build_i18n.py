#!/usr/bin/env python3
"""Vuahem i18n generator + language gate.

Source of truth: i18n/pairs.json — {"exact": {English: Vietnamese}, "frag": {…}}.
The page carries both renderings of every covered run:

    <span class="i18n"><span lang="en">English</span><span lang="vi">Vietnamese</span></span>

so the switch only flips <html lang> and CSS hides one half. No translation table
lives in the page, and no sentence can end up half in one language: the two
renderings ship together or not at all.

    python3 tools/build_i18n.py            # rebuild index.html from the dictionary
    python3 tools/build_i18n.py --check    # report drift and coverage, change nothing
    python3 tools/build_i18n.py --self-test

Why a generator instead of a page-side dictionary: a dictionary matched against
innerhtml silently accepts a wrong pair. Three holes it could never close — a key
whose text is real but whose markup the key does not cover ("VAT &amp; e-invoice"
compared against escaped text and never matching), a selector that matched script
code instead of copy, and a run no dictionary can express ("From " + "$49/month").
A stale pair inside an already-wrapped body also counted as done, so editing the
dictionary changed nothing and CI stayed green.

Rules: copy is matched in text runs only — tags, <script> and <style> are never
copy, so a key cannot be satisfied by a selector. Keys apply longest first, and
runs over 40 characters need a whole-run match, so a long sentence is never served
by one of its own words. Vietnamese is escaped on the way in. Keys that match
nothing are reported, never counted as done: that is data, not a gate, or the gate
decays into --force.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DICT = ROOT / "i18n" / "pairs.json"
PAGE = ROOT / "index.html"
MIN_KEYS = 30          # below this a gate would pass any page
MIN_COVERAGE = 0.75    # share of bilingual runs that must carry a rendering
LONG_RUN = 40          # longer copy is translated whole or not at all
LANG = re.compile(r"(?<![A-Za-z])(vi|zh|ja)(?![A-Za-z])")
UNIT = re.compile(r'<span class="i18n">((?:\s*<span lang="[a-z]{2}">[^<]*</span>\s*)+)</span>')
HALVES = re.compile(r'<span lang="([a-z]{2})">([^<]*)</span>')


def html_escape(s):
    """Escape for HTML text content. Module-level so helpers do not reach for
    xml.etree's different escaping."""
    return html.escape(s, quote=False)


def lang_of(vi):
    m = LANG.search(vi)
    return m.group(1) if m else "vi"


def load_pairs(path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    out = [{"en": html.unescape(k), "vi": html.unescape(v), "mode": "exact"}
           for k, v in (raw.get("exact") or {}).items()]
    out += [{"en": html.unescape(k), "vi": html.unescape(v), "mode": "frag"}
            for k, v in (raw.get("frag") or {}).items()]
    return out


def runs(doc):
    """Markup as (kind, text) pieces; only 'text' is copy."""
    out, i, n = [], 0, len(doc)
    code = re.compile(r"<(script|style)\b.*?</\1\s*>", re.S | re.I)
    while i < n:
        if doc[i] == "<":
            m = code.match(doc, i)
            if m:
                out.append(("code", m.group(0)))
                i = m.end()
                continue
            j = doc.find(">", i)
            j = n - 1 if j < 0 else j
            out.append(("tag", doc[i:j + 1]))
            i = j + 1
        else:
            j = doc.find("<", i)
            j = n if j < 0 else j
            out.append(("text", doc[i:j]))
            i = j
    return out


def strip_units(doc):
    """Back to plain copy: the English half is what a rebuild re-translates. A
    unit with English only keeps its English; a unit whose only half is Vietnamese
    is dropped as dead markup rather than left to pile up on the next rebuild."""
    def flat(m):
        halves = HALVES.findall(m.group(1))
        en = [t for l, t in halves if l == "en"]
        return en[0] if en else ""
    return UNIT.sub(flat, doc)


def unit(en, vi):
    return ('<span class="i18n"><span lang="en">%s</span><span lang="%s">%s</span></span>'
            % (html_escape(en), lang_of(vi), html_escape(vi)))


def translate(doc, pairs):
    """Wrap covered copy. Longest key first, and both sides compared unescaped so
    a key written with &amp; and copy written with &amp; are the same text."""
    pairs = sorted(pairs, key=lambda p: -len(p["en"]))
    out, used = [], set()
    for kind, chunk in runs(doc):
        if kind != "text" or not chunk.strip():
            out.append(chunk)
            continue
        plain = html.unescape(chunk)
        taken, marks = [], []
        for p in pairs:
            en, vi = html.unescape(p["en"]), html.unescape(p["vi"])
            if len(en) > LONG_RUN and p["mode"] == "frag":
                continue
            if p["mode"] == "exact":
                m = re.search(re.escape(en), plain)
                hits = [(m.start(), m.end())] if m and plain.strip() == en else []
            else:
                flags = re.I if len(en) <= LONG_RUN else 0
                pat = re.compile(r"(?<![\w&])%s(?![\w;])" % re.escape(en), flags)
                hits = [(m.start(), m.end()) for m in pat.finditer(plain)]
            for s, e in hits:
                if any(s < t1 and t0 < e for t0, t1 in taken):
                    continue
                taken.append((s, e))
                marks.append((s, e, vi, p["en"]))
        if not marks:
            out.append(chunk)
            continue
        marks.sort()
        built, at = "", 0
        for s, e, vi, key in marks:
            built += plain[at:s] + unit(plain[s:e], vi)
            at = e
            used.add(key)
        out.append(built + plain[at:])
    return "".join(out), used


def render_vi(doc):
    """What a Vietnamese reader sees: every unit's English half dropped."""
    return UNIT.sub(lambda m: "".join(t for l, t in HALVES.findall(m.group(1))
                                      if l != "en"), doc)


def english_runs(doc):
    """English text runs a reader could still be handed: copy of 4+ ASCII letters
    with no Vietnamese in it."""
    return [t.strip() for kind, t in runs(doc) if kind == "text"
            for t in [re.sub(r"<[^>]+>", " ", html.unescape(t))]
            if re.search(r"[A-Za-z]{4}", t) and not re.search(r"[^\x00-\x7F]", t)]


def coverage(doc):
    """Share of bilingual runs carrying a non-English rendering. Page-wide English
    text would pass on a page where nothing translates, so only i18n runs count."""
    units = UNIT.findall(doc)
    done = sum(1 for u in units
               if any(l != "en" and re.search(r"[^\x00-\x7F]", t)
                      for l, t in HALVES.findall(u)))
    return done, len(units)


def english_only(doc):
    """Units with an English half and no rendering — the silent-acceptance shape.
    Legal and brand copy is allowed to stay English; everything else is a gap."""
    return [t for u in UNIT.findall(doc)
            for parts in [HALVES.findall(u)]
            if [l for l, _ in parts] == ["en"] and len(parts[0][1].strip()) > 3
            for t in [parts[0][1]]]


FIXTURES = [
    ("amp-key",
     "<p>VAT &amp; e-invoice checked against the Tax Dept DB</p>",
     [("VAT &amp; e-invoice checked against the Tax Dept DB",
       "Hoá đơn &amp; e-invoice đối chiếu CSDL cơ quan thuế", "exact")],
     lambda out: "lang=\"vi\"" in out and "VAT &" not in render_vi(out)),
    ("word-fragment",
     "<p>Digital Tax Compliance Infrastructure</p>",
     [("Digital Tax", "Thuế", "frag"),
      ("Digital Tax Compliance Infrastructure", "Hạ tầng tuân thủ thuế kỹ thuật số", "exact")],
     lambda out: "Compliance Infrastructure" not in render_vi(out)),
    ("script-selector",
     '<script>document.querySelectorAll("VAT &amp; e-invoice")</script>'
     '<p>Unrelated copy about pricing</p>',
     [("VAT &amp; e-invoice", "Hoá đơn", "frag")],
     lambda out: "i18n" not in out),
]


def self_test():
    """These three go red if the silent-acceptance bugs come back."""
    bad = []
    for name, page, pairs, ok in FIXTURES:
        out = translate(page, [{"en": e, "vi": v, "mode": m} for e, v, m in pairs])[0]
        if not ok(out):
            bad.append("fixture %s accepted a wrong pair: %s" % (name, render_vi(out)))
    return bad


def main():
    if "--self-test" in sys.argv:
        bad = self_test()
        for b in bad:
            print("FAIL:", b)
        print("self-test: %s" % ("%d fixtures FAILED" % len(bad) if bad
                                 else "%d fixtures behaved" % len(FIXTURES)))
        return 1 if bad else 0
    if not DICT.exists():
        print("FAIL: no dictionary at %s" % DICT)
        return 1
    pairs = load_pairs(DICT)
    if len(pairs) < MIN_KEYS:
        print("FAIL: only %d keys — a dictionary this small proves nothing "
              "(CI can bypass a minimum). Refusing to run." % len(pairs))
        return 1
    bad = self_test()
    page = PAGE.read_text(encoding="utf-8")
    rebuilt, used = translate(strip_units(page), pairs)
    done, total = coverage(page)
    rebuilt_done, _ = coverage(rebuilt)
    unused = sorted(p["en"] for p in pairs if p["en"] not in used
                    and html.unescape(p["en"]) not in html.unescape(page))
    lost = [u for u in english_only(rebuilt) if u not in english_only(page)]
    if "--check" in sys.argv:
        if total and done / total < MIN_COVERAGE:
            bad.append("coverage %.0f%% of %d bilingual runs is under the %.0f%% "
                       "minimum" % (100 * done / total, total, 100 * MIN_COVERAGE))
        if rebuilt_done < done:
            bad.append("a rebuild would lose %d of the %d renderings the page "
                       "carries now — dictionary gaps inside copy that is already "
                       "bilingual; fix the pairs before regenerating"
                       % (done - rebuilt_done, done))
        for b in bad:
            print("FAIL:", b)
        if bad:
            return 1
        if unused:
            print("note: %d keys match nothing on the page (data, not a gate): %s"
                  % (len(unused), "; ".join(unused[:6])))
        print("ok: %d pairs, %d/%d bilingual runs rendered (%.0f%%), %d keys "
              "unmatchable by design" % (len(pairs), done, total,
              100 * done / total if total else 100, len(unused)))
        return 0
    if rebuilt == page:
        print("index.html matches i18n/pairs.json (%d pairs, %d unmatchable)"
              % (len(pairs), len(unused)))
        return 0
    if lost:
        print("refusing to rewrite index.html: a rebuild would drop %d renderings "
              "the page carries now (%s). Add those pairs first."
              % (len(lost), "; ".join(lost[:4])))
        return 1
    PAGE.write_text(rebuilt, encoding="utf-8")
    print("rebuilt index.html: %d/%d pairs placed, %d matched nothing"
          % (len(pairs) - len(unused), len(pairs), len(unused)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
