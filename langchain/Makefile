.PHONY: install lint format typecheck test check
install:
	pip install -r requirements-dev.txt && pre-commit install && pre-commit install --hook-type pre-push
lint:
	ruff check .
format:
	ruff format .
typecheck:
	mypy
test:
	pytest
check: lint typecheck test
