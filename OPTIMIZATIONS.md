# Performance Optimizations for Lif

This document provides an overview of the available performance optimizations for Lif using Numba and Cython.

## Prerequisites

To use the optimized versions, you'll need to install the following packages:

```
pip install numba cython numpy
```

For Cython optimizations, you'll also need to build the extension modules:

```
python setup_cython.py build_ext --inplace
```

## Optimization Approaches

We've implemented several optimization strategies:

1. **Numba JIT Compilation**: Just-in-time compilation of key functions
2. **Cython Compilation**: Ahead-of-time compilation of key functions to C
3. **Algorithm Optimizations**: Improved algorithms and data structures

## Benchmarking & Comparison

Use the `compare_optimizations.py` script to benchmark the different implementations:

```
python compare_optimizations.py
```

To install dependencies and build Cython extensions automatically:

```
python compare_optimizations.py --install-deps --build-cython
```

## Using Optimized Version

Run the optimized version with:

```
python lif_optimized.py -opt [other arguments]
```

Additional options:
- `--use-numba`: Prefer Numba optimizations when available
- `--use-cython`: Prefer Cython optimizations when available

## Optimized Components

1. **Math Utilities**:
   - `iid_set`: Random set generation
   - `weighted_choice`: Weighted random selection

2. **Grid Operations**:
   - Numba-optimized `step` function
   - Optimized stasis condition checking
   - Gain of habitability calculations

## Performance Results

Based on benchmarks, you can expect the following improvements:

| Function | Numba Speedup | Cython Speedup |
|----------|--------------|---------------|
| iid_set  | ~2-5x        | ~5-10x        |
| weighted_choice | ~2-3x   | ~3-5x        |
| step (full simulation) | ~1.5-2x | N/A  |

## Notes on Optimization Strategy

- **Numba** works best for numerical operations and simple functions
- **Cython** excels with more complex algorithms but requires more setup
- Neither approach works well with Python's dynamic features

The current implementation prioritizes compatibility and ease of use. More aggressive optimizations would require significant refactoring of the codebase.