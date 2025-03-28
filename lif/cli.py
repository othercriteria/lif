#!/usr/bin/env python
"""Command-line interface for Lif"""

import curses
import cProfile
import random
import argparse
from typing import Any, Optional

from .config import params, parse_args, update_params

def run() -> None:
    """Main entry point for the application"""
    # Get and process command line arguments
    args = parse_args()
    update_params(args)
    
    # Import after params update
    from .core import main, do_sim
    
    # Set args so they can be accessed in the simulation
    from . import core
    core.args = args
    
    if args.timing:
        import cProfile

        # For consistent simulation outcome
        random.seed(137)

        if args.blind:
            cProfile.run('from lif.core import do_sim; do_sim(None, None, None, None)')
        else:
            cProfile.run('import curses; from lif.core import main; curses.wrapper(main)')
    else:
        curses.wrapper(main)

if __name__ == "__main__":
    run()