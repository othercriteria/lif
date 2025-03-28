#!/usr/bin/env python
"""Command-line interface for Lif"""

import curses
import random
import sys
import argparse

from .config import parse_args, update_params

# Try to import optimized modules
try:
    from .utils.numba_optimized import numba_iid_set, numba_weighted_choice, NUMBA_AVAILABLE
except ImportError:
    NUMBA_AVAILABLE = False
    print("Numba optimizations not available.")

try:
    from .utils.cython_optimized import cy_iid_set, cy_weighted_choice
    CYTHON_AVAILABLE = True
except ImportError:
    CYTHON_AVAILABLE = False
    print("Cython optimizations not available.")

# Import step optimizer if available
try:
    from .grid_numba import optimize_step
    STEP_OPTIMIZER_AVAILABLE = True
except ImportError:
    STEP_OPTIMIZER_AVAILABLE = False
    print("Step optimizer not available.")

# Import original step function for optimization
from .grid import step as original_step


def optimize_functions():
    """Apply optimizations to key functions"""
    if not (NUMBA_AVAILABLE or CYTHON_AVAILABLE):
        print("No optimizations available.")
        return False
    
    print("Applying optimizations...")
    
    # Apply chosen optimizations (numba/cython) to key functions
    # This approach monkey-patches the original module functions with optimized versions
    from . import utils
    
    if CYTHON_AVAILABLE:
        print("Using Cython optimizations for math functions.")
        utils.math.iid_set = cy_iid_set
        utils.math.weighted_choice = cy_weighted_choice
    elif NUMBA_AVAILABLE:
        print("Using Numba optimizations for math functions.")
        utils.math.iid_set = numba_iid_set
        utils.math.weighted_choice = numba_weighted_choice
        
    # Optimize the step function if available
    if STEP_OPTIMIZER_AVAILABLE:
        print("Using optimized step function.")
        from . import grid
        optimized_step = optimize_step(original_step)
        grid.step = optimized_step
    
    return True

def parse_extended_args():
    """Parse optimization-related arguments"""
    ext_parser = argparse.ArgumentParser(add_help=False)
    ext_parser.add_argument('--no-optimize', action='store_true',
                            help='Disable optimizations (use original implementation)')
    ext_parser.add_argument('--use-numba', action='store_true',
                            help='Prefer Numba optimizations if available')
    ext_parser.add_argument('--use-cython', action='store_true',
                            help='Prefer Cython optimizations if available')
    
    # Parse just optimization arguments
    ext_args, remaining = ext_parser.parse_known_args()
    
    # Restore sys.argv for original parser
    sys.argv = [sys.argv[0]] + remaining
    
    return ext_args

def run() -> None:
    """Main entry point for the application"""
    # Parse optimization args first
    opt_args = parse_extended_args()
    
    # Get and process command line arguments
    args = parse_args()
    update_params(args)
    
    # Apply optimizations by default unless disabled
    if not opt_args.no_optimize:
        optimize_functions()
    
    # Important: Re-initialize grid after updating parameters
    from .grid import initialize_grid
    initialize_grid()
    
    # Import after params update
    # Set args so they can be accessed in the simulation
    from . import core
    from .core import main
    core.args = args  # type: ignore
    
    # Handle blind mode or profiling
    if args.blind or args.timing:
        import cProfile

        # For consistent simulation outcome
        random.seed(137)

        if args.blind:
            cProfile.run('from lif.core import do_sim; do_sim(None, None, None, None)')
        else:
            cProfile.run('import curses; from lif.core import main; curses.wrapper(main)')
    else:
        # Try to run with curses, fall back to blind mode if it fails
        try:
            curses.wrapper(main)
        except Exception as e:
            print(f"Error initializing curses: {e}")
            print("Falling back to blind mode with 10 generations...")
            from .core import do_sim
            do_sim(None, None, None, None)

if __name__ == "__main__":
    run()