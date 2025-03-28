.PHONY: help install dev test lint typecheck format clean all optimize benchmark

help:
	@echo "lif - Game of Life variant with local dynamics"
	@echo ""
	@echo "make help       - Show this help message"
	@echo "make install    - Install the package"
	@echo "make dev        - Install the package in development mode"
	@echo "make test       - Run tests"
	@echo "make lint       - Run linting"
	@echo "make typecheck  - Run type checking"
	@echo "make format     - Format code"
	@echo "make clean      - Clean build artifacts"
	@echo "make all        - Run lint, typecheck, and test"
	@echo "make optimize   - Build optimized Cython modules"
	@echo "make benchmark  - Run benchmarks to compare optimizations"

install:
	pip install .

dev:
	pip install -e .

test:
	PYTHONPATH=. python -m unittest discover -s tests

lint:
	ruff check lif/

typecheck:
	mypy --python-version 3.8 lif/

format:
	ruff format lif/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf __pycache__
	rm -rf lif/__pycache__
	rm -rf lif/**/__pycache__
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf *.so
	rm -rf lif/**/*.so
	rm -rf *.c
	rm -rf lif/**/*.c

optimize:
	python setup_cython.py build_ext --inplace

benchmark:
	python compare_optimizations.py

deep-optimize:
	python deeper_optimization.py --compare --size 50 --generations 100

profile:
	python deeper_optimization.py --profile --size 50 --generations 50

all: lint typecheck test