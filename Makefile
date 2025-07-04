.PHONY: build test lint

build:
	hatch build

test:
	PYTHONPATH=src python -m pytest -vv

lint:
	ruff check .
