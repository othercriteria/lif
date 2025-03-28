#!/usr/bin/env python
"""Tests for optimized mutate function"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import time
import random

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import original mutate function
from lif.models import Alive, mutate as original_mutate
from lif.stasis import s_set, set_to_stasis

# Define optimized version
def optimized_mutate(parent: Alive) -> Alive:
    """Create a mutated version of the parent cell"""
    # Import inside function to match original
    from lif.config import params
    from lif.utils.math import iid_set
    
    # Early exit if mutation rate is zero
    mut_p = params['mut_p']
    if mut_p <= 0:
        return parent
    
    # Generate mutation set
    mut = iid_set(mut_p)
    if not mut:  # Empty set check is faster than sum(mut) > 0
        return parent
    
    # Apply mutation when needed
    new_stasis_mut = s_set[parent.stasis].symmetric_difference(mut)
    return parent.child(set_to_stasis(new_stasis_mut))

class TestOptimizedMutate(unittest.TestCase):
    """Test cases for optimized mutate function"""
    
    def setUp(self):
        # Setup random seed for consistent results
        random.seed(42)
        
        # Create a test cell
        self.test_cell = Alive()
        self.test_cell.stasis = (True, True, True, False, False, False, False, False, False)
    
    @patch('lif.models.params', {'mut_p': 0.0})
    def test_mutate_no_mutation(self):
        """Test no mutation when probability is zero"""
        # Original function should return same cell
        result1 = original_mutate(self.test_cell)
        self.assertIs(result1, self.test_cell)
        
        # Optimized function should also return same cell
        result2 = optimized_mutate(self.test_cell)
        self.assertIs(result2, self.test_cell)
    
    @patch('lif.models.iid_set')
    @patch('lif.models.params', {'mut_p': 0.5})
    def test_mutate_with_empty_mutation_set(self, mock_iid_set):
        """Test with empty mutation set"""
        # Setup
        mock_iid_set.return_value = set()
        
        # Original function should return same cell
        result1 = original_mutate(self.test_cell)
        self.assertIs(result1, self.test_cell)
        
        # Optimized function with same mockup should return same cell
        with patch('lif.utils.math.iid_set', return_value=set()):
            result2 = optimized_mutate(self.test_cell)
            self.assertIs(result2, self.test_cell)
    
    @patch('lif.models.params', {'mut_p': 0.5})
    def test_mutate_correctness(self):
        """Test that optimized mutate gives same results as original"""
        # Setup multiple test cases with different random seeds
        for seed in range(10):
            # Reset seed for each test case
            random.seed(seed)
            
            # Run original mutate
            result1 = original_mutate(self.test_cell)
            stasis1 = result1.stasis
            
            # Reset seed for optimized version
            random.seed(seed)
            
            # Run optimized mutate
            result2 = optimized_mutate(self.test_cell)
            stasis2 = result2.stasis
            
            # Results should match
            self.assertEqual(stasis2, stasis1, f"Failed for seed {seed}")
    
    def test_mutate_performance(self):
        """Test performance improvement of optimized mutate"""
        iterations = 10000
        
        # Test with a small mutation probability like in real code
        with patch('lif.models.params', {'mut_p': 0.0001}):
            # Measure original function
            start = time.time()
            for _ in range(iterations):
                original_mutate(self.test_cell)
            original_time = time.time() - start
            
            # Reset test condition for optimized version
            with patch('lif.config.params', {'mut_p': 0.0001}):
                # Measure optimized function
                start = time.time()
                for _ in range(iterations):
                    optimized_mutate(self.test_cell)
                optimized_time = time.time() - start
        
        # Print performance comparison
        print(f"\nPerformance comparison for mutate:")
        print(f"Original: {original_time:.4f}s, Optimized: {optimized_time:.4f}s")
        print(f"Speed improvement: {(original_time / optimized_time):.2f}x")
        
        # The optimized version should be faster
        self.assertLessEqual(optimized_time, original_time * 0.98)  # At least 2% faster

if __name__ == '__main__':
    unittest.main()