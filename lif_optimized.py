#!/usr/bin/env python
"""
Lif - Game of Life variant with local dynamics
Optimized version with Numba/Cython optimizations
"""

import sys
import os
import argparse
from typing import Dict, Any

# Import original modules
from lif.cli import run, parse_args, update_params
from lif.config import params
from lif.core import main, do_sim, args
from lif.grid import step as original_step

# Try to import optimized modules
try:
    from lif.utils.numba_optimized import numba_iid_set, numba_weighted_choice, NUMBA_AVAILABLE
except ImportError:
    NUMBA_AVAILABLE = False
    print("Numba optimizations not available.")

try:
    from lif.utils.cython_optimized import cy_iid_set, cy_weighted_choice
    CYTHON_AVAILABLE = True
except ImportError:
    CYTHON_AVAILABLE = False
    print("Cython optimizations not available.")

# Import step optimizer
try:
    from lif.grid_numba import optimize_step
    STEP_OPTIMIZER_AVAILABLE = True
except ImportError:
    STEP_OPTIMIZER_AVAILABLE = False
    print("Step optimizer not available.")

def optimize_functions():
    """Apply optimizations to key functions"""
    if not (NUMBA_AVAILABLE or CYTHON_AVAILABLE):
        print("No optimizations available.")
        return False
    
    print("Applying optimizations...")
    
    # Apply chosen optimizations (numba/cython) to key functions
    # This approach monkey-patches the original module functions with optimized versions
    
    import lif.utils.math
    if NUMBA_AVAILABLE:
        print("Using Numba optimizations for math functions.")
        lif.utils.math.iid_set = numba_iid_set
        lif.utils.math.weighted_choice = numba_weighted_choice
    elif CYTHON_AVAILABLE:
        print("Using Cython optimizations for math functions.")
        lif.utils.math.iid_set = cy_iid_set
        lif.utils.math.weighted_choice = cy_weighted_choice
    
    # Optimize the step function if available
    import lif.grid
    if STEP_OPTIMIZER_AVAILABLE:
        print("Using optimized step function.")
        optimized_step = optimize_step(original_step)
        lif.grid.step = optimized_step
    
    return True

def parse_extended_args():
    """Parse the original args and add optimization options"""
    # Parse original args first
    original_parser = argparse.ArgumentParser(add_help=False)
    original_parser.add_argument('-opt', '--optimize', action='store_true',
                            help='Use optimized implementations where available')
    original_parser.add_argument('--use-numba', action='store_true',
                            help='Prefer Numba optimizations if available')
    original_parser.add_argument('--use-cython', action='store_true',
                            help='Prefer Cython optimizations if available')
    
    # Parse just our arguments first
    args, remaining = original_parser.parse_known_args()
    
    # Then pass the rest to the original parser
    sys.argv = [sys.argv[0]] + remaining
    original_args = parse_args()
    
    return args, original_args

if __name__ == "__main__":
    # Parse extended arguments
    extended_args, original_args = parse_extended_args()
    
    # Apply optimizations if requested
    if extended_args.optimize:
        optimize_functions()
    
    # Update params with original args
    update_params(original_args)
    
    # Run the simulation
    run()