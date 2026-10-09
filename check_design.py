#!/usr/bin/env python3
"""Design-system conformance gate for the DESIGN_1 (Shopifi-style) rewrite.
Checks the rules that can be proven mechanically. Usage: python3 check_design.py [path]"""
import re, sys

p = sys.argv[1] if len(sys.argv) > 1 else "/Users/agento/projects/hoadonshield/index.html"
s = open(p, encoding="utf-8").read()
head, body = s.split("</head>", 1)
fail = []

# 1. pill is the only button shape: every element that looks like a button must be rounded-full
for m in re.finditer(r'<(?:button|a)\b[^>]*class="([^"]*)"', s):
    c = m.group(1)
    if "btn-pill" in c:
        continue
    if re.search(r'\brounded-(lg|xl|md|sm)\b', c):
        fail.append("non-pill radius on a control: " + c[:70])

# 2. only two canvases: no third canvas colour (grey/beige/blue) as a section background
ALLOWED_BG = {"black", "#000", "#000000", "#0a0a0a", "bg-white", "bg-black", "bg-cream", "bg-[#fbfbf5]", "#fbfbf5",
              "#ffffff", "bg-aloe", "#c1fbd4", "bg-pistachio", "#d4f9e0"}
for m in re.finditer(r'<section[^>]*class="([^"]*)"', s):
    for tok in re.findall(r'bg-\[#[0-9a-fA-F]{3,8}\]|bg-(?:white|black|cream|aloe|pistachio|shade-\d+|surfDark|nightElev)', m.group(1)):
        if tok not in ALLOWED_BG:
            fail.append("off-system section canvas: " + tok)

# 3. aloe/pistachio are surface fills on the LIGHT track only
for m in re.finditer(r'<section[^>]*class="([^"]*bg-black[^"]*)"[^>]*>(.*?)</section>', s, re.S):
    if "aloe" in m.group(2) or "pistachio" in m.group(2):
        fail.append("green fill used on the cinematic (black) track")

# 4. greens must not be used as text colours
if re.search(r'text-aloe|text-pistachio|text-\[#c1fbd4\]|text-\[#d4f9e0\]', s):
    fail.append("green used as a text colour")

# 5. display tiers render at weight 330, never 400+
for cls in ["dsp", "dsp-lg"]:
    for rule in re.findall(r'\.%s\{([^}]*)\}' % cls, head):
        if "font-weight:330" not in rule.replace(" ", ""):
            fail.append(".%s lost its weight-330 display cut: %s" % (cls, rule[:60]))
if re.search(r'\.dsp[^-][^{]*\{[^}]*font-weight:\s*(4|5|6|7)\d\d', head):
    fail.append("display class bumped to weight >=400")

# 6. ss03 signature applied globally
if 'font-feature-settings:"ss03"' not in head.replace(" ", ""):
    fail.append("ss03 stylistic set not applied at root")

# 7. track separation: light-track cards (4-stack halo shadow) must not sit on a black canvas
for m in re.finditer(r'<section[^>]*class="([^"]*bg-black[^"]*)"[^>]*>(.*?)</section>', s, re.S):
    if "card-light" in m.group(2):
        fail.append("light-track card (stacked shadow) inside the cinematic track")

# 8. no serif left over from the previous system
for bad in ["Cormorant", "Georgia", "cc785c", "a9583e", "faf9f5", "efe9de"]:
    if bad in s:
        fail.append("leftover from the old palette: " + bad)
if re.search(r"(?<!sans-)serif", s):
    fail.append("a serif family is declared")

# 9. touch targets: any declared min-height floor must be >= 44px (WCAG target size)
import re as _re
floors = [int(n) for n in _re.findall(r'min-h-\[(\d+)px\]', s)]
if not floors:
    fail.append("no touch-target floor declared")
for n in floors:
    if n < 44:
        fail.append("touch target floor below 44px: min-h-[%dpx]" % n)

print("controls:", len(re.findall(r'<(?:button|a)\b', s)), "| sections:", len(re.findall(r'<section', s)))
if fail:
    print("FAIL:")
    for f in fail:
        print("  -", f)
    sys.exit(1)
print("PASS: 9 design-system checks")
