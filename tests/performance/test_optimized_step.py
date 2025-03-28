#!/usr/bin/env python
"""Tests for optimizing the step function in the simulation"""

import unittest
import sys
import os
import time
import random
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the original step function to have as a baseline
from lif.grid import step as original_step

# Import other required modules
from lif.models import Alive, Empty, empty_init

def create_test_grid(size=10):
    """Create a test grid of cells for simulation"""
    from lif.models import Alive, Empty
    
    # Create grid
    grid = {}
    for x in range(size):
        for y in range(size):
            # Place some alive cells randomly
            if random.random() < 0.3:
                cell = Alive()
                grid[(x, y)] = cell
            else:
                grid[(x, y)] = Empty()
    
    return grid

def create_test_nbrs(grid, size=10):
    """Create test neighbor structure"""
    # Create neighborhood mappings
    live_nbrs = {}
    live_nbrs_num = {}
    
    # Helper to get neighbors for a position
    def get_neighbors(x, y):
        neighbors = []
        for nx in range(max(0, x-1), min(size, x+2)):
            for ny in range(max(0, y-1), min(size, y+2)):
                if nx == x and ny == y:
                    continue
                neighbors.append((nx, ny))
        return neighbors
    
    # Initialize neighbor lists
    for x in range(size):
        for y in range(size):
            pos = (x, y)
            live_nbrs[pos] = []
            live_nbrs_num[pos] = 0
    
    # Populate alive neighbors
    for x in range(size):
        for y in range(size):
            pos = (x, y)
            if grid[pos].alive:
                for n in get_neighbors(x, y):
                    live_nbrs[n].append(pos)
                    live_nbrs_num[n] += 1
    
    return live_nbrs, live_nbrs_num

class TestStepOptimization(unittest.TestCase):
    """Tests for step function optimization"""
    
    def setUp(self):
        """Setup common test data"""
        # Fix random seed
        random.seed(42)
        
        # Create test grid and neighbors
        self.size = 20
        self.grid = create_test_grid(self.size)
        self.live_nbrs, self.live_nbrs_num = create_test_nbrs(self.grid, self.size)
        
        # Create new grid and neighbor structures for the next step
        self.grid_new = {}
        self.live_nbrs_new = {}
        self.live_nbrs_num_new = {}
        
        for pos in self.live_nbrs:
            self.live_nbrs_new[pos] = self.live_nbrs[pos][:]
            self.live_nbrs_num_new[pos] = self.live_nbrs_num[pos]
    
    def test_original_step(self):
        """Test the original step function"""
        # Patch random functions for deterministic results
        with patch('lif.grid.random.choice', return_value=0):
            with patch('lif.grid.runif', return_value=0.5):
                # Run the step
                events = original_step(
                    self.grid, self.grid_new, 
                    self.live_nbrs, self.live_nbrs_new,
                    self.live_nbrs_num, self.live_nbrs_num_new
                )
                
                # Basic validation
                self.assertIsInstance(events, dict)
                # Grid should be updated
                self.assertTrue(len(self.grid_new) > 0)
    
    def time_step(self, iterations=10):
        """Time the step function performance"""
        # Create multiple grids to avoid reusing the same grid
        grids = []
        for _ in range(iterations):
            # New random grid for each iteration
            random.seed()
            g = create_test_grid(self.size)
            ln, lnn = create_test_nbrs(g, self.size)
            grids.append((g, ln, lnn))
        
        # Measure original step function
        start = time.time()
        for i in range(iterations):
            g, ln, lnn = grids[i]
            g_new = {}
            ln_new = {}
            lnn_new = {}
            for pos in ln:
                ln_new[pos] = ln[pos][:]
                lnn_new[pos] = lnn[pos]
            
            # Run step
            original_step(g, g_new, ln, ln_new, lnn, lnn_new)
        
        original_time = time.time() - start
        
        return original_time

if __name__ == '__main__':
    # Run the tests
    unittest.main()