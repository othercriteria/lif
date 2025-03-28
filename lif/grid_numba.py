"""
Numba-optimized versions of grid functions
"""

try:
    from numba import jit, njit
    import numpy as np
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if args and callable(args[0]) else decorator
    
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if args and callable(args[0]) else decorator

import random
from typing import Dict, Tuple, List, Any, Set

# Import base implementations
from .grid import settlement, exchange
from .utils.math import runif

# Type aliases for clarity
GridLocation = Tuple[int, int]
StasisArray = Tuple[bool, bool, bool, bool, bool, bool, bool, bool, bool]

@njit(cache=True)
def numba_check_stasis(stasis: StasisArray, nb_num: int) -> bool:
    """Optimized version of checking stasis condition"""
    return stasis[nb_num]

@njit(cache=True)
def numba_apply_goh(stasis: StasisArray, mode: str = 'max') -> StasisArray:
    """Apply gain of habitability to stasis"""
    # Create a new stasis array
    new_stasis = list(stasis)
    
    # Find indices where stasis is True
    indices = []
    for i in range(len(stasis)):
        if stasis[i]:
            indices.append(i)
    
    if not indices:
        return stasis  # No change if no bits are set
    
    # Pick an index to clear based on mode
    if mode == 'min':
        idx = min(indices)
    elif mode == 'max':
        idx = max(indices)
    else:  # 'random'
        idx = indices[random.randint(0, len(indices) - 1)]
    
    # Clear the bit
    new_stasis[idx] = False
    
    return tuple(new_stasis)

def optimize_step(step_func):
    """
    Decorator to optimize the step function without changing its signature.
    This doesn't modify the original function but creates an optimized version.
    """
    def optimized_step(grid_old, grid_new, live_nbrs_old, live_nbrs_new, 
                       live_nbrs_num_old, live_nbrs_num_new):
        """Optimized version of step function"""
        # Get references to functions we'll need
        from .config import params
        from .models import Alive, Empty, empty_init
        from math import exp
        
        # Just use the original function if Numba is not available
        if not NUMBA_AVAILABLE:
            return step_func(grid_old, grid_new, live_nbrs_old, live_nbrs_new, 
                            live_nbrs_num_old, live_nbrs_num_new)
                            
        # The rest follows the original step function logic but
        # with Numba-optimized calls where possible
        
        # Determine active gain of habitability mechanism
        if params['goh_m'] == 'max':
            def goh(cell):
                return Empty(numba_apply_goh(cell.stasis, 'max'))
        elif params['goh_m'] == 'min':
            def goh(cell):
                return Empty(numba_apply_goh(cell.stasis, 'min'))
        elif params['goh_m'] == 'random':
            def goh(cell):
                return Empty(numba_apply_goh(cell.stasis, 'random'))
        
        # Precompute cost function
        cost_func = {}
        f = params['fit_cost']
        for s in range(10):
            cost_func[s] = exp(-f * s)
        
        events = {}
        goh_r = params['goh_r']
        exchange_r = params['exchange_r']
        
        # Loop through grid cells (main simulation loop)
        from .grid import neighborhood
        for loc in grid_old:
            cell = grid_old[loc]
            nb_num = live_nbrs_num_old[loc]
            
            # Check stasis condition (optimized)
            if numba_check_stasis(cell.stasis, nb_num):
                if not cell.alive:
                    grid_new[loc] = goh(cell) if runif() < goh_r else cell
                else:
                    if nb_num == 0 or runif() >= exchange_r:
                        grid_new[loc] = cell
                    else:
                        new, conspecific = exchange(loc, grid_old, live_nbrs_old)
                        grid_new[loc] = new
                        events[loc] = 'exchange conspecific' if conspecific else 'exchange interspecific'
            else:
                # Gain or loss
                if not cell.alive:
                    if nb_num == 0:
                        grid_new[loc] = Alive()
                        for n in neighborhood[loc]:
                            live_nbrs_new[n].append(loc)
                            live_nbrs_num_new[n] += 1
                    else:
                        grid_new[loc] = settlement(loc, grid_old, live_nbrs_old, cost_func)
                        for n in neighborhood[loc]:
                            live_nbrs_new[n].append(loc)
                            live_nbrs_num_new[n] += 1
                        events[loc] = 'settlement'
                else:
                    grid_new[loc] = empty_init
                    for n in neighborhood[loc]:
                        live_nbrs_new[n].remove(loc)
                        live_nbrs_num_new[n] -= 1
        
        return events
    
    return optimized_step