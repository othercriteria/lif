"""
Cython-optimized versions of key functions in Lif
"""
# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True

import random
from libc.stdlib cimport rand, RAND_MAX

cdef inline double c_random():
    """Fast random number generator"""
    return rand() / <double>RAND_MAX

def cy_iid_set(double p):
    """Cython-optimized version of iid_set"""
    # Special cases
    if p <= 0:
        return set()
    if p >= 1:
        return {0, 1, 2, 3, 4, 5, 6, 7, 8}
    
    # Create set directly for better performance
    cdef set result = set()
    cdef int s
    
    for s in range(9):
        if c_random() < p:
            result.add(s)
    
    return result

def cy_weighted_choice(list weights):
    """Cython-optimized version of weighted_choice"""
    cdef int n = len(weights)
    if n == 0:
        return 0
    if n == 1:
        return 0
    
    # Calculate sum
    cdef double total = 0.0
    cdef int i
    cdef double w
    
    for i in range(n):
        w = weights[i]
        total += w
    
    if total <= 0:
        return 0
    
    # Generate random point and find interval
    cdef double rnd = c_random() * total
    cdef double cumulative = 0.0
    
    for i in range(n):
        cumulative += weights[i]
        if cumulative > rnd:
            return i
    
    return n - 1