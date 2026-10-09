# Vuahem (vuahem.lol)

> Pre-filing input VAT and tax invoice risk audit platform.

Vuahem is an automated pre-filing invoice risk detection engine for Chief Accountants, CFOs, and business owners:
1. **Seller Tax Status Screening**: Real-time cross-referencing against statutory blacklists of suspended, closed, or relocated vendors.
2. **Issuance Timing Verification**: Flags invoices issued after official business suspension dates.
3. **3-Way Reconciliation**: Automated 3-way matching across XML/PDF Invoices ↔ Bank Statement Feeds (Payment Orders) ↔ Warehouse Receipts. Detects cash payments exceeding statutory thresholds.

---

## 3-Way Audit Engine Architecture

![Vuahem Architecture](assets/vuahem_diagram.png)

---

## Preview

![Landing Page Preview](assets/preview.png)

---

## Project Structure

Designed as a high-performance **single-file web application** with zero build dependencies:

- `index.html`: Complete landing page (Shopifi-inspired cinematic black & cream/mint design system, thin Grotesk display typography, and 100% pill-shaped controls).
- `check_design.py`: Automated design system conformance gate (9 mechanical checks: pill button geometry, canvas discipline, font scale, ss03, touch target floors).
- `verify.py`: Content and legal integrity gate (17 checks: banned claims scan, anchor integrity, interactive demo sanity).
- `BUILD_LOG.md`: Comprehensive engineering log and self-critique rounds with Claude Opus & GPT-6.1-sol.
- `assets/`: Architecture diagram and page previews.

---

## Local Development

No Node.js or build tools required:

```bash
# Option 1: Open directly in browser
open index.html

# Option 2: Run via local HTTP server
python3 -m http.server 8000
# Visit: http://localhost:8000
```

---

## Automated Quality Gates

Run checks prior to deployment:

```bash
# Verify design system compliance
python3 check_design.py index.html

# Verify content, anchors & disclaimers
python3 verify.py index.html
```

---

## Legal & Entity

**Vuahem Technologies Pte. Ltd.**  
68 Circular Road, #02-01, Singapore 049422  

© 2026 Vuahem Technologies Pte. Ltd. (vuahem.lol). Technical demonstration environment. Automated risk signals do not replace official statutory tax filings or determinations.
