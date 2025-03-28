"""Tests for math utilities"""

import unittest
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from lif.utils.math import iid_set, weighted_choice, gini

class TestMathUtils(unittest.TestCase):
    """Test cases for math utility functions"""
    
    @patch('lif.utils.math.runif')
    def test_iid_set_all_below_threshold(self, mock_runif):
        """Test iid_set when all random values are below threshold"""
        # Arrange
        mock_runif.side_effect = [0.1, 0.2, 0.3, 0.1, 0.2, 0.3, 0.1, 0.2, 0.3]
        
        # Act
        result = iid_set(0.5)
        
        # Assert
        self.assertEqual(result, {0, 1, 2, 3, 4, 5, 6, 7, 8})
        self.assertEqual(mock_runif.call_count, 9)
    
    @patch('lif.utils.math.runif')
    def test_iid_set_all_above_threshold(self, mock_runif):
        """Test iid_set when all random values are above threshold"""
        # Arrange
        mock_runif.side_effect = [0.6, 0.7, 0.8, 0.6, 0.7, 0.8, 0.6, 0.7, 0.8]
        
        # Act
        result = iid_set(0.5)
        
        # Assert
        self.assertEqual(result, set())
        self.assertEqual(mock_runif.call_count, 9)
    
    @patch('lif.utils.math.runif')
    def test_iid_set_mixed_values(self, mock_runif):
        """Test iid_set with some values above and some below threshold"""
        # Arrange
        mock_runif.side_effect = [0.1, 0.6, 0.2, 0.7, 0.3, 0.8, 0.4, 0.9, 0.5]
        
        # Act
        result = iid_set(0.5)
        
        # Assert
        self.assertEqual(result, {0, 2, 4, 6, 8})
        self.assertEqual(mock_runif.call_count, 9)
    
    def test_iid_set_edge_cases(self):
        """Test iid_set edge cases for p=0 and p=1"""
        # p=0 should always return an empty set
        self.assertEqual(iid_set(0), set())
        
        # p=1 should always return {0,1,2,3,4,5,6,7,8}
        self.assertEqual(iid_set(1), {0, 1, 2, 3, 4, 5, 6, 7, 8})
    
    @patch('lif.utils.math.runif')
    def test_weighted_choice_first_weight(self, mock_runif):
        """Test weighted_choice selects first weight"""
        # Arrange
        mock_runif.return_value = 0.1
        weights = [1.0, 2.0, 3.0]
        
        # Act
        result = weighted_choice(weights)
        
        # Assert
        self.assertEqual(result, 0)
    
    @patch('lif.utils.math.runif')
    def test_weighted_choice_middle_weight(self, mock_runif):
        """Test weighted_choice selects middle weight"""
        # Arrange
        mock_runif.return_value = 0.4
        weights = [1.0, 2.0, 3.0]  # Total 6, rnd is 0.4*6=2.4
        
        # Act
        result = weighted_choice(weights)
        
        # Assert
        self.assertEqual(result, 1)
    
    @patch('lif.utils.math.runif')
    def test_weighted_choice_last_weight(self, mock_runif):
        """Test weighted_choice selects last weight"""
        # Arrange
        mock_runif.return_value = 0.9
        weights = [1.0, 2.0, 3.0]  # Total 6, rnd is 0.9*6=5.4
        
        # Act
        result = weighted_choice(weights)
        
        # Assert
        self.assertEqual(result, 2)
    
    def test_weighted_choice_edge_cases(self):
        """Test weighted_choice edge cases"""
        # Empty weights should return 0
        self.assertEqual(weighted_choice([]), 0)
        
        # Single weight should return 0
        self.assertEqual(weighted_choice([5.0]), 0)
        
        # All zero weights should return 0
        self.assertEqual(weighted_choice([0.0, 0.0, 0.0]), 0)
    
    def test_gini_coefficient(self):
        """Test gini coefficient calculation"""
        # Equal distribution should have gini close to 0
        data = [(10, 'A'), (10, 'B'), (10, 'C')]
        self.assertAlmostEqual(gini(data), 0.0, places=6)
        
        # Unequal distribution should have higher gini
        data = [(10, 'A'), (5, 'B'), (1, 'C')]
        self.assertGreater(gini(data), 0.3)
        
        # Perfect inequality (one has everything)
        data = [(10, 'A'), (0, 'B'), (0, 'C')]
        self.assertAlmostEqual(gini(data), 0.6666666, places=6)
        
        # Empty list should return 0
        self.assertEqual(gini([]), 0.0)

if __name__ == '__main__':
    unittest.main()