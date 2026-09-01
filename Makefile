PY ?= .venv/bin/python

.PHONY: setup lint test reqs loop check

setup:
	python3 -m venv .venv && $(PY) -m pip install -q -r requirements.txt

lint:
	$(PY) -m ruff check .

test:
	$(PY) -m pytest -q -p no:cacheprovider || [ $$? -eq 5 ]

reqs:
	$(PY) scripts/check_requirements.py

loop:
	$(PY) scripts/harness/check_loop.py

check: lint test reqs loop
