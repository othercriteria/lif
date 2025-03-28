"""Tests for grid functions"""

import unittest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from lif.grid import settlement, exchange, neighbors
from lif.models import Alive, Empty
from lif.stasis import stasis_all, s_count, s_set

class TestGridFunctions(unittest.TestCase):
    """Tests for grid-related functions"""
    
    @patch('lif.grid.params', {'size': {'x': 5, 'y': 5}, 'toroidal': True})
    def test_neighbors_toroidal(self):
        """Test neighbor calculation with toroidal grid"""
        # Center location should have 8 neighbors
        center_loc = (2, 2)
        nbrs = neighbors(center_loc)
        self.assertEqual(len(nbrs), 8)
        
        # Corner should still have 8 neighbors in toroidal mode
        corner_loc = (0, 0)
        nbrs = neighbors(corner_loc)
        self.assertEqual(len(nbrs), 8)
        
        # Check corner wrapping
        self.assertIn((4, 4), nbrs)  # Opposite corner
    
    @patch('lif.grid.params', {'size': {'x': 5, 'y': 5}, 'toroidal': False})
    def test_neighbors_nontoroidal(self):
        """Test neighbor calculation with non-toroidal grid"""
        # Center location should have 8 neighbors
        center_loc = (2, 2)
        nbrs = neighbors(center_loc)
        self.assertEqual(len(nbrs), 8)
        
        # Corner should only have 3 neighbors in non-toroidal mode
        corner_loc = (0, 0)
        nbrs = neighbors(corner_loc)
        self.assertEqual(len(nbrs), 3)
        self.assertIn((0, 1), nbrs)
        self.assertIn((1, 0), nbrs)
        self.assertIn((1, 1), nbrs)
    
    @patch('lif.grid.weighted_choice')
    def test_settlement(self, mock_weighted_choice):
        """Test settlement function"""
        # Setup
        mock_weighted_choice.return_value = 0
        
        loc = (2, 2)
        neighbor_loc = (1, 1)
        
        # Create a parent cell with known stasis
        with patch('lif.utils.math.iid_set') as mock_iid_set:
            mock_iid_set.return_value = {0, 1, 2}
            parent_cell = Alive()
        
        # Mock grid and neighbor structure
        grid_old = {neighbor_loc: parent_cell}
        live_nbrs_old = {loc: [neighbor_loc]}
        
        # Mock cost function
        cost_func = {s: 1.0 for s in range(10)}
        
        # Test the settlement function - with no mutation
        with patch('lif.grid.mutate', return_value=parent_cell) as mock_mutate:
            settled = settlement(loc, grid_old, live_nbrs_old, cost_func)
            
            # Settlement should call weighted_choice and mutate
            mock_weighted_choice.assert_called_once()
            mock_mutate.assert_called_once_with(parent_cell)
            
            # Result should be the parent cell (since we mocked mutate)
            self.assertEqual(settled, parent_cell)
    
    @patch('lif.grid.random.choice')
    def test_exchange_conspecific(self, mock_choice):
        """Test exchange with conspecific neighbors"""
        # Setup - both cells have same parent
        parent_id = 42
        loc = (2, 2)
        nbr_loc = (1, 1)
        
        # Create cells with different stasis but same parent
        cell1_stasis = (True, True, False, False, False, False, False, False, False)
        cell2_stasis = (False, False, True, True, False, False, False, False, False)
        
        cell1 = Alive(blank=True)
        cell1.parent = parent_id
        cell1.stasis = cell1_stasis
        
        cell2 = Alive(blank=True)
        cell2.parent = parent_id
        cell2.stasis = cell2_stasis
        
        # Setup grid and neighbors
        grid_old = {loc: cell1, nbr_loc: cell2}
        live_nbrs_old = {loc: [nbr_loc]}
        
        # Mock random choice to return our neighbor
        mock_choice.return_value = nbr_loc
        
        # Mock random values for genetic exchange (50% chance per gene)
        with patch('lif.grid.runif') as mock_runif:
            # For genes 0,1,2,3 we'll use probabilities 0.4, 0.6, 0.4, 0.6
            # This means we keep genes 0,2 from cell1 and take 1,3 from cell2
            mock_runif.side_effect = [0.4, 0.6, 0.4, 0.6]
            
            # Disable mutation
            with patch('lif.grid.mutate', side_effect=lambda x: x):
                # Test exchange
                result, is_conspecific = exchange(loc, grid_old, live_nbrs_old)
                
                # Should be marked as conspecific
                self.assertTrue(is_conspecific)
                
                # Should have combined genes with 50% probability
                expected_stasis = (True, False, False, True, False, False, False, False, False)
                self.assertEqual(result.stasis, expected_stasis)
                
                # Should maintain parent ID
                self.assertEqual(result.parent, parent_id)
    
    def test_exchange_identical_stasis(self):
        """Test exchange with identical stasis (no change)"""
        # Setup - cells with same stasis
        parent_id = 42
        loc = (2, 2)
        nbr_loc = (1, 1)
        
        stasis = (True, True, False, False, False, False, False, False, False)
        
        cell1 = Alive(blank=True)
        cell1.parent = parent_id
        cell1.stasis = stasis
        
        cell2 = Alive(blank=True)
        cell2.parent = parent_id
        cell2.stasis = stasis
        
        # Setup grid and neighbors
        grid_old = {loc: cell1, nbr_loc: cell2}
        live_nbrs_old = {loc: [nbr_loc]}
        
        # Mock random choice
        with patch('lif.grid.random.choice', return_value=nbr_loc):
            # Disable mutation 
            with patch('lif.grid.mutate', side_effect=lambda x: x):
                # Test exchange
                result, is_conspecific = exchange(loc, grid_old, live_nbrs_old)
                
                # Should be marked as conspecific
                self.assertTrue(is_conspecific)
                
                # Should keep the same stasis since they're identical
                self.assertEqual(result.stasis, stasis)
                self.assertEqual(result.parent, parent_id)

if __name__ == '__main__':
    unittest.main()