#!/usr/bin/env python3
"""Verification gate for the landing page: banned phrases, dangling anchors, JS sanity.
Supports both English and Vietnamese text.
Usage: python3 verify.py [path]  -> exit 1 on any failure."""
import re, sys

p = sys.argv[1] if len(sys.argv) > 1 else "/Users/agento/projects/vuahem/index.html"
s = open(p, encoding="utf-8").read()
fail = []

# absolute claims / unverifiable promises that must never appear
BANNED = [
    "0 rủi ro", "0 risk", "zero risk",
    "100% Xác thực", "100% Guaranteed",
    "cơ sở dữ liệu rủi ro quốc gia",
    "Đồng bộ Dữ liệu Tổng cục Thuế",
    "bảo hiểm bồi thường",
    "024 0000", "đang cập nhật", "Hotline",
    "Đặt lịch demo 30 phút", "mst&&mst.length>=10",
    "0317892140"
]
for b in BANNED:
    if b.lower() in s.lower():
        fail.append("banned phrase: " + b)

# every in-page anchor must resolve
ids = set(re.findall(r'id="([A-Za-z]+)"', s))
for h in set(re.findall(r'href="#([A-Za-z]+)"', s)):
    if h not in ids and h != "main":
        fail.append("dangling anchor: #" + h)

# every id referenced from JS must exist in the markup
for i in set(re.findall(r"getElementById\('([A-Za-z]+)'\)", s)):
    if 'id="%s"' % i not in s:
        fail.append("JS references missing id: " + i)

# demo data must be labelled as illustrative
if "Dữ liệu minh họa" not in s and "illustrative" not in s.lower():
    fail.append("illustrative-data disclaimer missing")

# section order: proof before price, integrations after price
order = re.findall(r'<section id="([a-z]+)"', s)
if "pricing" in order and "integrations" in order:
    if order.index("pricing") > order.index("integrations"):
        fail.append("integrations still before pricing")
if "roi" in order and "pricing" in order:
    if order.index("roi") > order.index("pricing"):
        fail.append("ROI proof sits after pricing")

print("section order:", " -> ".join(order))
if fail:
    print("FAIL:")
    for f in fail:
        print("  -", f)
    sys.exit(1)
print("PASS: %d checks, %d chars" % (len(BANNED) + 3, len(s)))
