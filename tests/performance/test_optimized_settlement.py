#!/usr/bin/env python
"""Tests for optimized settlement function"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import time
import random

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import original function
from lif.grid import settlement as original_settlement
from lif.models import Alive, Empty
from lif.stasis import s_count

# Define optimized version
def optimized_settlement(
    loc,
    grid_old,
    live_nbrs_old,
    cost_func
):
    """Create a new settlement from neighboring cells"""
    # Optimization: access live_nbrs_old[loc] once
    neighbors = live_nbrs_old[loc]
    
    # No need to calculate probabilities if there's only one neighbor
    if len(neighbors) == 1:
        settler = grid_old[neighbors[0]]
        from lif.models import mutate
        return mutate(settler)
    
    # Pre-calculate probabilities for weighted choice
    from lif.utils.math import weighted_choice
    probs = [cost_func[s_count[grid_old[n].stasis]] for n in neighbors]
    settler = grid_old[neighbors[weighted_choice(probs)]]
    
    from lif.models import mutate
    return mutate(settler)

class TestOptimizedSettlement(unittest.TestCase):
    """Test cases for optimized settlement function"""
    
    def setUp(self):
        # Setup test data
        self.loc = (2, 2)
        self.neighbors = [(1, 1), (1, 2), (1, 3)]
        
        # Create cells with different stasis patterns
        self.cells = {}
        for i, pos in enumerate(self.neighbors):
            cell = Alive()
            # Create different stasis values
            cell.stasis = tuple([i == j for j in range(9)])
            self.cells[pos] = cell
        
        # Create grid and neighbors
        self.grid_old = self.cells
        self.live_nbrs_old = {self.loc: self.neighbors}
        
        # Create cost function
        self.cost_func = {s: 1.0/(s+1) for s in range(10)}
    
    @patch('lif.grid.weighted_choice')
    @patch('lif.grid.mutate')
    def test_settlement_single_neighbor(self, mock_mutate, mock_weighted_choice):
        """Test settlement with a single neighbor"""
        # Setup - only one neighbor
        live_nbrs_single = {self.loc: [self.neighbors[0]]}
        
        # Create mock return values
        expected_cell = Alive()
        mock_mutate.return_value = expected_cell
        
        # Test original function
        result1 = original_settlement(self.loc, self.grid_old, live_nbrs_single, self.cost_func)
        
        # Verify behavior
        self.assertEqual(result1, expected_cell)
        mock_weighted_choice.assert_called()  # Original still calls weighted_choice
        
        # Reset mocks for optimized function
        mock_mutate.reset_mock()
        mock_weighted_choice.reset_mock()
        
        # Test optimized function
        with patch('lif.models.mutate', return_value=expected_cell):
            result2 = optimized_settlement(self.loc, self.grid_old, live_nbrs_single, self.cost_func)
        
        # Optimized should not call weighted_choice for single neighbor
        self.assertEqual(result2, expected_cell)
        mock_weighted_choice.assert_not_called()
    
    @patch('lif.utils.math.runif')
    def test_settlement_correctness(self, mock_runif):
        """Test that optimized settlement gives same results as original"""
        # Fix random values for deterministic results
        mock_runif.return_value = 0.5
        
        with patch('lif.grid.mutate', side_effect=lambda x: x):
            # Test original settlement
            result1 = original_settlement(self.loc, self.grid_old, self.live_nbrs_old, self.cost_func)
            
            # Test optimized settlement
            with patch('lif.models.mutate', side_effect=lambda x: x):
                result2 = optimized_settlement(self.loc, self.grid_old, self.live_nbrs_old, self.cost_func)
            
            # Results should be the same
            self.assertEqual(result2.stasis, result1.stasis)
    
    def test_settlement_performance(self):
        """Test performance improvement of optimized settlement"""
        iterations = 10000
        
        # Make sure each function has identical random state during the test
        with patch('lif.utils.math.runif', return_value=0.5):
            with patch('lif.grid.mutate', side_effect=lambda x: x):
                # Measure original function with many neighbors
                start = time.time()
                for _ in range(iterations):
                    original_settlement(self.loc, self.grid_old, self.live_nbrs_old, self.cost_func)
                original_many_time = time.time() - start
                
                # Measure original function with single neighbor
                start = time.time()
                for _ in range(iterations):
                    original_settlement(self.loc, self.grid_old, {self.loc: [self.neighbors[0]]}, self.cost_func)
                original_single_time = time.time() - start
                
                # Measure optimized function with many neighbors
                with patch('lif.models.mutate', side_effect=lambda x: x):
                    start = time.time()
                    for _ in range(iterations):
                        optimized_settlement(self.loc, self.grid_old, self.live_nbrs_old, self.cost_func)
                    optimized_many_time = time.time() - start
                    
                    # Measure optimized function with single neighbor
                    start = time.time()
                    for _ in range(iterations):
                        optimized_settlement(self.loc, self.grid_old, {self.loc: [self.neighbors[0]]}, self.cost_func)
                    optimized_single_time = time.time() - start
        
        # Print performance comparison
        print(f"\nPerformance comparison for settlement (many neighbors):")
        print(f"Original: {original_many_time:.4f}s, Optimized: {optimized_many_time:.4f}s")
        print(f"Speed improvement: {(original_many_time / optimized_many_time):.2f}x")
        
        print(f"\nPerformance comparison for settlement (single neighbor):")
        print(f"Original: {original_single_time:.4f}s, Optimized: {optimized_single_time:.4f}s")
        print(f"Speed improvement: {(original_single_time / optimized_single_time):.2f}x")
        
        # The optimized version should be faster, especially for single neighbor case
        self.assertLessEqual(optimized_many_time, original_many_time)
        self.assertLessEqual(optimized_single_time, original_single_time * 0.9)  # At least 10% faster

if __name__ == '__main__':
    unittest.main()