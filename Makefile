# Verification chain for the landing page. `make check` must stay at zero failures;
# a build whose Vietnamese render is identical to English is a broken build, not a
# clean one, which is what verify_i18n.js exists to catch.
PYTHON ?= python3
NODE ?= node
PAGE ?= index.html

check:
	$(PYTHON) verify.py $(PAGE)
	$(PYTHON) check_design.py
	$(NODE) tools/check_lang.js $(PAGE)
	$(NODE) tools/verify_i18n.js $(PAGE)

# Drift gate, run before committing: fails if index.html no longer matches
# i18n/pairs.json.
drift:
	$(PYTHON) tools/build_i18n.py --check

i18n:
	$(PYTHON) tools/build_i18n.py

.PHONY: check drift i18n
