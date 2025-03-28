# Tests for Lif

This directory contains unit tests and performance tests for the Lif simulation.

## Running Tests

To run all tests:

```bash
make test
```

Or run individual test modules:

```bash
python -m unittest tests/test_math.py
```

## Test Organization

- `grid/`: Tests for grid-related functionality
- `lif/`: Tests for core Lif functionality
- `performance/`: Performance benchmarks and optimization tests

## Performance Testing

To run performance tests and optimizations:

```bash
# Build Cython extensions
make optimize

# Run performance benchmarks
make benchmark
```