"""Math utilities for Lif"""

from random import random as runif
from typing import Any, List, Set, Tuple, TypeVar

T = TypeVar('T')

def iid_set(p: float) -> Set[int]:
    """Create a set with independent probability p for each element"""
    # Performance optimization: avoid creating set comprehension for common cases
    if p <= 0:
        return set()
    if p >= 1:
        return set(range(9))
    
    # Use direct set construction for better performance
    result = set()
    for s in range(9):
        if runif() < p:
            result.add(s)
    return result

def weighted_choice(weights: List[float]) -> int:
    """
    Weighted random selection
    Based on: http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python
    Optimized version with O(1) sum calculation and improved early return
    """
    # Handle common cases
    n = len(weights)
    if n == 0:
        return 0
    if n == 1:
        return 0
    
    # Pre-calculate sum
    total = sum(weights)
    if total <= 0:
        return 0  # Avoid division by zero
    
    # Generate random point and find the interval it falls in
    rnd = runif() * total
    cumulative = 0
    for i, w in enumerate(weights):
        cumulative += w
        if cumulative > rnd:  # Changed from rnd < 0 to avoid subtraction
            return i
    return n - 1  # Fallback

def gini(ys: List[Tuple[int, Any]]) -> float:
    """
    Calculate the Gini coefficient
    See http://en.wikipedia.org/wiki/Gini_coefficient for formula
    """
    n = len(ys)
    sy, siy = 0, 0
    if n > 0:
        for i, y in enumerate(sorted(ys, key=lambda p: p[0])):
            sy += y[0]
            siy += y[0] * (i+1)
        return 2 * siy / (n * sy) - (n + 1) / n
    else:
        return 0.0