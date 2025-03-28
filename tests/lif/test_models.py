"""Tests for cell models"""

import unittest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from lif.models import Alive, Empty, mutate
from lif.stasis import StasisKey, stasis_all

class TestModels(unittest.TestCase):
    """Tests for cell model classes and functions"""
    
    def test_empty_cell_creation(self):
        """Test creating empty cells"""
        # Test default Empty initialization
        cell = Empty()
        self.assertFalse(cell.alive)
        self.assertEqual(cell.stasis, stasis_all)
        
        # Test Empty with custom stasis
        custom_stasis = (True, False, True, False, True, False, True, False, True)
        cell = Empty(custom_stasis)
        self.assertFalse(cell.alive)
        self.assertEqual(cell.stasis, custom_stasis)
    
    def test_alive_cell_creation(self):
        """Test creating alive cells"""
        # Test with mocked stasis generation
        with patch('lif.models.iid_set') as mock_iid_set:
            mock_iid_set.return_value = {0, 3, 6}
            cell = Alive()
            self.assertTrue(cell.alive)
            # Check that the parent ID was assigned
            self.assertGreater(cell.parent, 0)
            # Check stasis was created from iid_set result
            self.assertEqual(
                cell.stasis, 
                (True, False, False, True, False, False, True, False, False)
            )
    
    def test_alive_child_creation(self):
        """Test creating a child cell from a parent"""
        # Create a parent cell
        parent = Alive()
        parent_id = parent.parent
        
        # Create child with custom stasis
        custom_stasis: StasisKey = (False, True, False, True, False, True, False, True, False)
        child = parent.child(custom_stasis)
        
        # Child should inherit parent's ID but have different stasis
        self.assertTrue(child.alive)
        self.assertEqual(child.parent, parent_id)
        self.assertEqual(child.stasis, custom_stasis)
    
    @patch('lif.models.params', {'mut_p': 0.0})
    def test_mutate_no_mutation(self):
        """Test mutate function with mutation probability 0"""
        # Arrange
        parent = Alive()
        parent_stasis = parent.stasis
        
        # Act
        mutated = mutate(parent)
        
        # Assert - with p=0, should return same cell
        self.assertIs(mutated, parent)
        self.assertEqual(mutated.stasis, parent_stasis)
    
    @patch('lif.models.params', {'mut_p': 0.5})
    @patch('lif.models.iid_set')
    def test_mutate_with_empty_mutation_set(self, mock_iid_set):
        """Test mutate function with empty mutation set"""
        # Arrange
        mock_iid_set.return_value = set()  # No mutations
        parent = Alive()
        parent_stasis = parent.stasis
        
        # Act
        mutated = mutate(parent)
        
        # Assert - empty mutation set should return same cell
        self.assertIs(mutated, parent)
        self.assertEqual(mutated.stasis, parent_stasis)
    
    @patch('lif.models.params', {'mut_p': 0.5})
    @patch('lif.models.iid_set')
    def test_mutate_with_mutation(self, mock_iid_set):
        """Test mutate function with non-empty mutation set"""
        # Arrange - create a cell with known stasis
        with patch('lif.utils.math.iid_set') as mock_cell_iid:
            mock_cell_iid.return_value = {0, 1, 2}
            parent = Alive()  # stasis will be (True, True, True, False, False, False, False, False, False)
        
        # Set mutation at positions 2 and 3
        mock_iid_set.return_value = {2, 3}
        
        # Act
        mutated = mutate(parent)
        
        # Assert
        self.assertIsNot(mutated, parent)  # Should be a new cell
        self.assertEqual(mutated.parent, parent.parent)  # Should keep parent ID
        
        # Expected stasis after mutation (flip positions 2 and 3)
        expected_stasis = (True, True, False, True, False, False, False, False, False)
        self.assertEqual(mutated.stasis, expected_stasis)

if __name__ == '__main__':
    unittest.main()