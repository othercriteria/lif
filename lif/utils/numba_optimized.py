"""
Numba-optimized versions of key functions in Lif
"""
try:
    from numba import jit, njit
    NUMBA_AVAILABLE = True
except ImportError:
    # Fall back to dummy decorators if Numba is not available
    NUMBA_AVAILABLE = False
    
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if args and callable(args[0]) else decorator
    
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if args and callable(args[0]) else decorator

import random
from typing import List, Set, Tuple
from random import random as runif

# Optimized version of iid_set
@njit(cache=True)
def numba_iid_set(p: float) -> Set[int]:
    """Numba-accelerated version of iid_set"""
    # Special cases
    if p <= 0:
        return set()
    if p >= 1:
        return {0, 1, 2, 3, 4, 5, 6, 7, 8}
    
    # Create set directly for better performance
    result = set()
    for s in range(9):
        if random.random() < p:
            result.add(s)
    return result

# Optimized version of weighted_choice
@njit(cache=True)
def numba_weighted_choice(weights: List[float]) -> int:
    """Numba-accelerated version of weighted_choice"""
    n = len(weights)
    if n == 0:
        return 0
    if n == 1:
        return 0
    
    # Calculate sum
    total = 0.0
    for w in weights:
        total += w
    
    if total <= 0:
        return 0
    
    # Generate random point and find interval
    rnd = random.random() * total
    cumulative = 0.0
    for i in range(n):
        cumulative += weights[i]
        if cumulative > rnd:
            return i
    
    return n - 1

# Helper functions for testing
def test_original_vs_numba(iterations=10000):
    """Test original vs. Numba versions"""
    from time import time
    from ..utils.math import iid_set, weighted_choice
    
    # Test iid_set
    print("Testing iid_set performance...")
    start = time()
    for _ in range(iterations):
        iid_set(0.5)
    original_time = time() - start
    
    start = time()
    for _ in range(iterations):
        numba_iid_set(0.5)
    numba_time = time() - start
    
    print(f"Original: {original_time:.4f}s, Numba: {numba_time:.4f}s")
    print(f"Speedup: {original_time/numba_time:.2f}x")
    
    # Test weighted_choice
    weights = [1.0, 2.0, 3.0, 4.0, 5.0]
    print("\nTesting weighted_choice performance...")
    start = time()
    for _ in range(iterations):
        weighted_choice(weights)
    original_time = time() - start
    
    start = time()
    for _ in range(iterations):
        numba_weighted_choice(weights)
    numba_time = time() - start
    
    print(f"Original: {original_time:.4f}s, Numba: {numba_time:.4f}s")
    print(f"Speedup: {original_time/numba_time:.2f}x")

# Only run the test if this module is executed directly
if __name__ == "__main__":
    test_original_vs_numba()