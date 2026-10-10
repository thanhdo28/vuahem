#!/usr/bin/env python3
"""Keep the Vuahem landing page's Vietnamese half in sync with the English half.

index.html holds ONE source for both languages. Static copy is wrapped into
`<span class="i18n"><span lang="en">…</span><span lang="vi">…</span></span>`
pairs (page CSS renders whichever matches <html lang>); script-rendered copy
carries its own {en, vi} pairs. Translations live in i18n/pairs.json.

Re-run after editing English copy: new strings report as MISS (translation
needed), stale keys report too, so the Vietnamese half can't drift silently.

Usage:  python3 tools/build_i18n.py [--check]
  --check  report only; exit 1 when a rebuild is pending or a pair went stale.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"
PAIRS = json.loads((ROOT / "i18n" / "pairs.json").read_text(encoding="utf-8"))
check = "--check" in sys.argv
orig = src = HTML.read_text(encoding="utf-8")
misses, wrapped = [], 0


def protected(txt):
    """Ranges never edited: script/style/textarea bodies."""
    return [(m.start(), m.end())
            for tag in ("script", "style", "textarea")
            for m in re.finditer(r"<%s\b.*?</%s>" % (tag, tag), txt, re.S)]


def in_text(txt, i, spans):
    """True when position i sits inside a text node, not markup or script."""
    if any(a <= i < b for a, b in spans):
        return False
    j = i - 1
    while j >= 0:
        if txt[j] == ">":
            return True
        if txt[j] == "<":
            return False
        j -= 1
    return True


def wrap(txt, key, val, exact):
    """Wrap every clean text occurrence of key. Returns (text, count).

    exact   → the key is a whole text node (matched as >KEY<).
    prefix  → the key ends with a space, so it is a label prefix inside a longer
              node ("Form: ", "Tel: "); the text after it may be anything.
    frag    → a phrase inside a longer node; both neighbours must be non-word
              characters, and a whole-node match is left to the exact pass.
    """
    spans = protected(txt)
    prefix = (not exact) and key.endswith(" ")
    exact_keys = PAIRS["exact"]
    hits, i = [], 0
    while True:
        needle = ">%s<" % key if exact else key
        i = txt.find(needle, i)
        if i < 0:
            break
        s, e = (i + 1, i + 1 + len(key)) if exact else (i, i + len(key))
        if not exact:
            a, b = txt[s - 1:s], txt[e:e + 1]
            if prefix:
                if a not in (">", " ", ""):
                    i += 1
                    continue
            else:
                if re.match(r"[A-Za-z0-9]", a or " ") or re.match(r"[A-Za-z0-9]", b or " "):
                    i += 1
                    continue                   # word fragment
                if a == ">" and b == "<" and (s - 1, e) != (0, 0) and txt[s:e] in exact_keys:
                    i += 1
                    continue                   # whole node: the exact pass owns it
        if not in_text(txt, s, spans):
            i += 1
            continue
        if 'class="i18n"' in txt[max(0, s - 80):s]:
            i = e
            continue                           # already bilingual
        hits.append((s, e))
        i = e
    n = 0
    for s, e in sorted(hits, reverse=True):    # right→left keeps offsets valid
        pair = ('<span class="i18n"><span lang="en">%s</span><span lang="vi">%s</span></span>'
                % (txt[s:e], val.replace("&", "&amp;")))   # keep entities intact
        txt = txt[:s] + pair + txt[e:]
        n += 1
    return txt, n


def status(txt, key, val, exact):
    """'built' when the pair is already in the page, 'pending' when the English
    is there but unwrapped, 'absent' when the key matches nothing (stale entry).
    Ampersands are stored escaped in the page, so both spellings count as built."""
    for v in (val, val.replace("&", "&amp;")):
        if '<span lang="en">%s</span><span lang="vi">%s</span>' % (key, v) in txt:
            return "built"
    return "pending" if key in txt else "absent"


# longest keys first so a shorter key can't swallow part of a longer one
entries = sorted([("exact", k, v) for k, v in PAIRS["exact"].items()]
                 + [("frag", k, v) for k, v in PAIRS["frag"].items()],
                 key=lambda x: -len(x[1]))
states = {}
for mode, key, val in entries:
    st = status(src, key, val, mode == "exact")
    states.setdefault(st, []).append((mode, key))
    if st == "pending":
        src, n = wrap(src, key, val, mode == "exact")
        if n:
            wrapped += n
        else:
            misses.append((mode, key))       # present but unmatchable

# guard: the language machinery must stay in the page
guards = {
    "language switch buttons": 'class="langBtn',
    "language swap CSS": '.i18n>span{display:none}',
    "bilingual demo runtime": "function tx(",
}
broken = [name for name, needle in guards.items() if needle not in src]

def english_left(txt):
    """Visible text that is NOT already inside an .i18n pair — the coverage gap.
    Brand names, numbers and technical tokens are expected to stay as-is."""
    body = re.sub(r"<script>.*?</script>", "", txt, flags=re.S)
    body = re.sub(r"<style>.*?</style>", "", body, flags=re.S)
    body = re.sub(r'<span class="i18n">.*?</span></span>', "", body, flags=re.S)  # covered
    out = []
    for m in re.finditer(r">([^<>]{8,})<", body):
        s = " ".join(m.group(1).split())
        if re.search(r"[A-Za-z]{4}", s):
            out.append(s[:80])
    return out


if check:
    print("pairs built:", len(states.get("built", [])),
          "| need wrapping:", len(states.get("pending", [])),
          "| stale keys:", len(states.get("absent", [])))
    for a, b in states.get("pending", []):
        print("  TODO", a, "|", b[:70])
    for a, b in states.get("absent", []):
        print("  STALE (no such text in page)", a, "|", b[:70])
    left = english_left(src)
    print("unpaired English left:", len(left))
    for s2 in left[:12]:
        print("  LEFT |", s2)
    for b in broken:
        print("  BROKEN:", b)
    ok = src == orig and not broken and not states.get("pending") and not states.get("absent")
    print("state:", "in sync" if ok else "rebuild pending")
    sys.exit(0 if ok else 1)

HTML.write_text(src, encoding="utf-8")
print("wrapped:", wrapped, "| built pairs in page:", len(states.get("built", [])) + wrapped,
      "| stale keys:", len(states.get("absent", [])))
for a, b in states.get("absent", []):
    print("  STALE (no such text in page)", a, "|", b[:70])
for b in broken:
    print("  BROKEN:", b)
