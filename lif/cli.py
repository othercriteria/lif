#!/usr/bin/env python
"""Command-line interface for Lif"""

import curses
import random

from .config import parse_args, update_params


def run() -> None:
    """Main entry point for the application"""
    # Get and process command line arguments
    args = parse_args()
    update_params(args)
    
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