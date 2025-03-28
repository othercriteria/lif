"""Math utilities for Lif"""

from random import random as runif
from typing import Any, List, Set, Tuple, TypeVar

T = TypeVar('T')

def iid_set(p: float) -> Set[int]:
    """Create a set with independent probability p for each element"""
    return {s for s in range(9) if runif() < p}

def weighted_choice(weights: List[float]) -> int:
    """
    Weighted random selection
    Based on: http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python
    """
    rnd = runif() * sum(weights)
    for i, w in enumerate(weights):
        rnd -= w
        if rnd < 0:
            return i
    return len(weights) - 1  # Fallback

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