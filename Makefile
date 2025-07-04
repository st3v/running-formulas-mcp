.PHONY: help init build test lint clean release

help:
	@echo "Available targets:"
	@echo "  init              - Initialize development environment"
	@echo "  clean             - Clean build artifacts"
	@echo "  build             - Build the package"
	@echo "  test              - Run all tests"
	@echo "  tests             - Alias for 'test'"
	@echo "  lint              - Run linter on the codebase"
	@echo "  help              - Show this help message"
	@echo "  release           - Build and prepare for release"

# Initialize development environment
init:
	python -m venv .venv
	./.venv/bin/pip install --upgrade pip
	./.venv/bin/pip install -r requirements.txt
	@echo "Development environment initialized. Activate with: source .venv/bin/activate"

build: clean
	hatch build

test:
	PYTHONPATH=src python -m pytest -vv

tests: test

lint:
	ruff check .

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

release: clean build
	@echo "Package built and ready for release"
	@echo "Files in dist/:"
	@ls -la dist/
	twine upload dist/*
