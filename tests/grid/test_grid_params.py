#!/usr/bin/env python
"""Test grid parameter initialization"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_grid_params():
    """Test if grid parameters are properly updated"""
    from lif.config import params, update_params
    from lif.grid import valid_locs, neighborhood
    import argparse
    
    # Print initial values
    print(f"Initial grid size: {params['size']}")
    print(f"Initial valid_locs count: {len(valid_locs)}")
    print(f"Initial neighborhood count: {len(neighborhood)}")
    
    # Update params to a new size
    args = argparse.Namespace()
    args.width = 50
    args.height = 50
    args.alive_p = params['alive_p']
    args.mut_p = params['mut_p']
    args.exchange_r = params['exchange_r']
    args.goh_r = params['goh_r']
    args.pick = params['goh_m']
    args.fit_cost = params['fit_cost']
    args.nontoroidal = False
    args.output = params['outfile']
    
    update_params(args)
    
    # Call initialize_grid to update grid structures
    from lif.grid import initialize_grid
    initialize_grid()
    
    # Print updated values
    print(f"\nUpdated grid size: {params['size']}")
    print(f"Updated valid_locs count: {len(valid_locs)}")
    print(f"Updated neighborhood count: {len(neighborhood)}")
    
    # Check if they match
    expected_cells = args.width * args.height
    if len(valid_locs) != expected_cells:
        print(f"\n⚠️ ERROR: valid_locs was not updated! Expected {expected_cells}, got {len(valid_locs)}")
    if len(neighborhood) != expected_cells:
        print(f"⚠️ ERROR: neighborhood was not updated! Expected {expected_cells}, got {len(neighborhood)}")

if __name__ == "__main__":
    test_grid_params()