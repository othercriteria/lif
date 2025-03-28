# Performance Optimization Recommendations for Lif

This document tracks performance optimizations for Lif, including those already implemented and those still to be considered.

## Implemented Optimizations

The following optimizations have already been implemented:

### 1. Cache neighbor lookups in the main loop ✅

```python
# In grid.py:step()
for loc in grid_old:
    cell = grid_old[loc]
    nb_num = live_nbrs_num_old[loc]  # Cache this value
    
    # Safety check: ensure nb_num is within bounds of stasis
    if nb_num >= len(cell.stasis):
        nb_num = len(cell.stasis) - 1
    
    if cell.stasis[nb_num]:
        # ...
```

### 2. Optimize the `settlement` function for single neighbor case ✅

```python
# In grid.py:settlement()
def settlement(loc, grid_old, live_nbrs_old, cost_func):
    """Create a new settlement from neighboring cells"""
    # Optimization: access live_nbrs_old[loc] once
    neighbors = live_nbrs_old[loc]
    
    # No need to calculate probabilities if there's only one neighbor
    if len(neighbors) == 1:
        settler = grid_old[neighbors[0]]
        # Safety check: ensure settler is Alive
        if not settler.alive:
            return Alive()  # Return a new Alive cell if settler isn't alive
        return mutate(settler)
    
    # Pre-calculate probabilities for weighted choice...
```

### 3. Initialize neighbor structures in batch ✅

```python
# In grid.py:initialize_grid()
def initialize_grid():
    """Initialize grid data structures based on current parameters"""
    global valid_locs, num_locs, neighborhood
    
    # Generate valid grid locations
    valid_locs = set(all_locs())
    num_locs = len(valid_locs)
    
    # Generate neighborhoods
    neighborhood = {}
    for loc in all_locs():
        neighborhood[loc] = neighbors(loc)
```

### 4. Cache parameter access in step function ✅

```python
# In grid.py:step()
events: Dict[GridLocation, str] = {}
goh_r = params['goh_r']  # Cache parameter access
exchange_r = params['exchange_r']  # Cache parameter access
```

### 5. Add bounds checking for stasis arrays ✅

```python
# In grid.py:step()
nb_num = live_nbrs_num_old[loc]  # Cache this value
    
# Safety check: ensure nb_num is within bounds of stasis
if nb_num >= len(cell.stasis):
    nb_num = len(cell.stasis) - 1
```

### 6. JIT Compilation with Numba ✅

Added Numba JIT compilation for key math functions.

### 7. Cython Optimization ✅

Added Cython implementations of performance-critical functions:
- `cy_iid_set`: 2.7-3.8x speedup
- `cy_weighted_choice`: 3.1-5.7x speedup

## Recommended Additional Optimizations

The following optimizations should still be considered:

### 1. Memoize the cost function calculation in `step()`

The cost function calculation can be memoized since it only depends on the `fit_cost` parameter:

```python
# Create a cache for cost functions with different fit_cost values
if not hasattr(step, 'cost_func_cache'):
    step.cost_func_cache = {}

# Use cached cost function if available
f = params['fit_cost']
if f not in step.cost_func_cache:
    cost_func = {}
    for s in range(10):
        cost_func[s] = exp(-f * s)
    step.cost_func_cache[f] = cost_func
else:
    cost_func = step.cost_func_cache[f]
```

### 2. Cache dictionary lookups in the `mutate` function

Further optimize the `mutate` function by caching the parent stasis set lookup:

```python
def mutate(parent):
    """Create a mutated version of the parent cell"""
    # Early exit if mutation rate is zero
    mut_p = params['mut_p']
    if mut_p <= 0:
        return parent
    
    # Generate mutation set
    mut = iid_set(mut_p)
    if not mut:  # Empty set check is faster than sum(mut) > 0
        return parent
    
    # Apply mutation
    parent_stasis_set = s_set[parent.stasis]  # Cache this lookup
    new_stasis_mut = parent_stasis_set.symmetric_difference(mut)
    return parent.child(set_to_stasis(new_stasis_mut))
```

### 3. Vectorization for grid operations

For larger grids, consider implementing NumPy-based vectorization:

```python
import numpy as np

# Example of vectorized cell processing
def process_cells_vectorized(grid, condition_matrix):
    # Process cells in batches using NumPy
    # ...
```

### 4. Precompute transition functions

Create lookup tables for common transition patterns:

```python
# Precompute common transitions
TRANSITION_TABLE = {}
for s in range(9):
    for alive in [True, False]:
        # Precompute results for this state
        # ...
```

## Performance Results

Benchmark results show improvements in two key areas:

1. **Math Functions**
   - `iid_set`: 1.0-1.1x speedup with Numba, 2.7-3.8x speedup with Cython
   - `weighted_choice`: Slowdown with Numba (0.06-0.12x), 3.1-5.7x speedup with Cython

2. **Data Structure Optimizations**
   - Original vs. optimized data structures: 1.0-1.1x speedup

The most significant gains come from Cython optimizations of the math functions.

The additional optimizations suggested here could potentially provide another 10-20% performance improvement, particularly for long-running simulations with large grid sizes.