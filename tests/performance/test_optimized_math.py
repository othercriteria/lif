#!/usr/bin/env python
"""Tests for optimized math utilities"""

import unittest
from unittest.mock import patch
import sys
import os
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Original functions
from lif.utils.math import iid_set as original_iid_set
from lif.utils.math import weighted_choice as original_weighted_choice

# Define optimized versions
def optimized_iid_set(p: float) -> set:
    """Create a set with independent probability p for each element"""
    # Performance optimization: avoid creating set comprehension for common cases
    if p <= 0:
        return set()
    if p >= 1:
        return set(range(9))
    
    # Use direct set construction for better performance
    from random import random as runif
    result = set()
    for s in range(9):
        if runif() < p:
            result.add(s)
    return result

def optimized_weighted_choice(weights):
    """
    Weighted random selection
    Optimized version with O(1) sum calculation and improved early return
    """
    # Handle common cases
    n = len(weights)
    if n == 0:
        return 0
    if n == 1:
        return 0
    
    # Pre-calculate sum
    from random import random as runif
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

class TestOptimizedMath(unittest.TestCase):
    """Test cases for optimized math utility functions"""
    
    def test_iid_set_correctness(self):
        """Test that optimized iid_set behaves the same as the original"""
        # Setup random seed for consistent results
        import random
        random.seed(42)
        
        # Test a range of probability values
        for p in [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]:
            # Reset seed for each test
            random.seed(42)
            expected = original_iid_set(p)
            
            # Reset seed to get same random values
            random.seed(42)
            actual = optimized_iid_set(p)
            
            # Results should be identical
            self.assertEqual(actual, expected, f"Failed for p={p}")
    
    def test_weighted_choice_correctness(self):
        """Test that optimized weighted_choice behaves the same as the original"""
        # Setup random seed for consistent results
        import random
        random.seed(42)
        
        # Test various weight distributions
        test_cases = [
            [1, 1, 1, 1],  # Equal weights
            [1, 2, 3, 4],  # Increasing weights
            [5, 0, 3, 0],  # Some zero weights
            [0, 0, 0, 1],  # Only one non-zero weight
            [0, 0, 0, 0],  # All zero weights
            [],            # Empty weights
            [42]           # Single weight
        ]
        
        for weights in test_cases:
            # Reset seed for each test
            random.seed(42)
            
            # Get a few samples from original
            original_samples = [original_weighted_choice(weights) for _ in range(10)]
            
            # Reset seed to get same random values
            random.seed(42)
            
            # Get samples from optimized version
            optimized_samples = [optimized_weighted_choice(weights) for _ in range(10)]
            
            # Results should be identical
            self.assertEqual(
                optimized_samples, 
                original_samples, 
                f"Failed for weights={weights}"
            )
    
    def test_iid_set_performance(self):
        """Test performance improvement of optimized iid_set"""
        iterations = 10000
        
        # Measure original function
        start = time.time()
        for _ in range(iterations):
            original_iid_set(0.5)
        original_time = time.time() - start
        
        # Measure optimized function
        start = time.time()
        for _ in range(iterations):
            optimized_iid_set(0.5)
        optimized_time = time.time() - start
        
        # Print performance comparison
        print(f"\nPerformance comparison for iid_set:")
        print(f"Original: {original_time:.4f}s, Optimized: {optimized_time:.4f}s")
        print(f"Speed improvement: {(original_time / optimized_time):.2f}x")
        
        # It should be at least as fast as the original
        self.assertLessEqual(optimized_time, original_time * 1.1)  # Allow for small variations
    
    def test_weighted_choice_performance(self):
        """Test performance improvement of optimized weighted_choice"""
        iterations = 10000
        weights = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        # Measure original function
        start = time.time()
        for _ in range(iterations):
            original_weighted_choice(weights)
        original_time = time.time() - start
        
        # Measure optimized function
        start = time.time()
        for _ in range(iterations):
            optimized_weighted_choice(weights)
        optimized_time = time.time() - start
        
        # Print performance comparison
        print(f"\nPerformance comparison for weighted_choice:")
        print(f"Original: {original_time:.4f}s, Optimized: {optimized_time:.4f}s")
        print(f"Speed improvement: {(original_time / optimized_time):.2f}x")
        
        # It should be at least as fast as the original
        self.assertLessEqual(optimized_time, original_time * 1.1)  # Allow for small variations

if __name__ == '__main__':
    unittest.main()