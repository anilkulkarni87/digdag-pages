.PHONY: install dev lint format test build run example clean

install:
	python -m pip install --upgrade pip
	pip install -e .

dev:
	python -m pip install --upgrade pip
	pip install -e .[dev]

lint:
	ruff check src tests

format:
	black src tests
	ruff check --fix src tests

test:
	pytest -q

build:
	python -m build

run:
	digdag-pages

example:
	cd examples && digdag-pages

clean:
	rm -rf build dist *.egg-info .pytest_cache __pycache__ graphs scheduled_workflows.html
