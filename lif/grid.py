"""Grid functions for Lif"""

import random
from math import exp
from typing import Any, Dict, Iterator, List, Set, Tuple

from .config import params
from .models import Alive, Empty, empty, empty_init, mutate
from .stasis import s_count, s_list, s_lose, s_lose_max, s_lose_min, s_set, set_to_stasis
from .utils.math import runif, weighted_choice

# Type definitions
GridLocation = Tuple[int, int]
Grid = Dict[GridLocation, Any]  # Will contain Alive or Empty objects
Neighborhood = Dict[GridLocation, Tuple[GridLocation, ...]]

def all_locs() -> Iterator[GridLocation]:
    """Generate all locations in the grid"""
    return (
        (x, y)
        for x in range(params['size']['x'])
        for y in range(params['size']['y'])
    )

# These will be initialized when initialize_grid() is called
valid_locs: Set[GridLocation] = set()
num_locs: int = 0
neighborhood: Neighborhood = {}

def neighbors(loc: GridLocation) -> Tuple[GridLocation, ...]:
    """Get all neighbors for a location"""
    x, y = loc

    if params['toroidal']:
        candidates = (
            (nx % params['size']['x'], ny % params['size']['y'])
            for nx in range(x - 1, x + 2)
            for ny in range(y - 1, y + 2)
            if not (nx == x and ny == y)
        )
    else:
        candidates = (
            (nx, ny)
            for nx in range(x - 1, x + 2)
            for ny in range(y - 1, y + 2)
            if not (nx == x and ny == y)
        )

    return tuple(c for c in candidates if c in valid_locs)

def initialize_grid():
    """Initialize grid data structures based on current parameters"""
    global valid_locs, num_locs, neighborhood
    
    # Generate valid grid locations
    valid_locs = set(all_locs())
    num_locs = len(valid_locs)
    
    # Generate neighborhoods
    neighborhood = {}
    for loc in all_locs():
        neighborhood[loc] = neighbors(loc)
        
# Initialize with default parameters
initialize_grid()

def settlement(
    loc: GridLocation,
    grid_old: Grid,
    live_nbrs_old: Dict[GridLocation, List[GridLocation]],
    cost_func: Dict[int, float]
) -> Alive:
    """Create a new settlement from neighboring cells"""
    # Optimization: access live_nbrs_old[loc] once
    neighbors = live_nbrs_old[loc]
    
    # No need to calculate probabilities if there's only one neighbor
    if len(neighbors) == 1:
        settler = grid_old[neighbors[0]]
        return mutate(settler)
    
    # Pre-calculate probabilities for weighted choice
    probs = [cost_func[s_count[grid_old[n].stasis]] for n in neighbors]
    settler = grid_old[neighbors[weighted_choice(probs)]]

    return mutate(settler)

def exchange(
    loc: GridLocation,
    grid_old: Grid,
    live_nbrs_old: Dict[GridLocation, List[GridLocation]]
) -> Tuple[Alive, bool]:
    """Exchange genetic material with neighboring cells"""
    exchangee = grid_old[loc]

    conspecific_nbrs = [n for n in live_nbrs_old[loc]
                      if grid_old[n].parent == exchangee.parent]
    conspecific = (len(conspecific_nbrs) > 0)
    if conspecific:
        exchanger_stasis = grid_old[random.choice(conspecific_nbrs)].stasis
    else:
        exchanger_stasis = grid_old[random.choice(live_nbrs_old[loc])].stasis
    
    p1, p2 = s_set[exchangee.stasis], s_set[exchanger_stasis]
    if p1 == p2:
        return mutate(exchangee), conspecific

    new_stasis = p1.intersection(p2)
    for s in p1.symmetric_difference(p2):
        if runif() < 0.5:
            new_stasis.add(s)
    exchangee_new = exchangee.child(set_to_stasis(new_stasis))
    return mutate(exchangee_new), conspecific

def step(
    grid_old: Grid,
    grid_new: Grid,
    live_nbrs_old: Dict[GridLocation, List[GridLocation]],
    live_nbrs_new: Dict[GridLocation, List[GridLocation]],
    live_nbrs_num_old: Dict[GridLocation, int],
    live_nbrs_num_new: Dict[GridLocation, int]
) -> Dict[GridLocation, str]:
    """Process one step of the simulation"""
    
    # Determine active gain of habitability mechanism
    if params['goh_m'] == 'max':
        def goh(cell: Empty) -> Empty:
            return empty[s_lose_max[cell.stasis]]
    elif params['goh_m'] == 'min':
        def goh(cell: Empty) -> Empty:
            return empty[s_lose_min[cell.stasis]]
    elif params['goh_m'] == 'random':
        def goh(cell: Empty) -> Empty:
            pick = random.choice(s_list[cell.stasis])
            return empty[s_lose[cell.stasis][pick]]

    # Precompute cost function for settlement
    # Cache this calculation outside the step function if params['fit_cost'] doesn't change
    cost_func = {}
    f = params['fit_cost']
    for s in range(10):
        cost_func[s] = exp(-f * s)
        
    events: Dict[GridLocation, str] = {}
    goh_r = params['goh_r']  # Cache parameter access
    exchange_r = params['exchange_r']  # Cache parameter access
    
    # Pre-fetch neighborhood to avoid dict lookups in the loop
    nbhood = neighborhood
    
    for loc in grid_old:
        cell = grid_old[loc]
        nb_num = live_nbrs_num_old[loc]  # Cache this value
        
        # Stasis condition - most common case first
        if cell.stasis[nb_num]:
            # Alive cells
            if cell.alive:
                # Most cells stay as they are - handle this case first for performance
                if nb_num == 0 or runif() >= exchange_r:
                    grid_new[loc] = cell
                else:
                    # Exchange case - less common
                    new, conspecific = exchange(loc, grid_old, live_nbrs_old)
                    grid_new[loc] = new
                    # Using string interning for event types
                    events[loc] = 'exchange conspecific' if conspecific else 'exchange interspecific'
            # Empty cells
            else:
                grid_new[loc] = goh(cell) if runif() < goh_r else cell
        else:
            # Gain or Loss conditions
            if not cell.alive:  # Empty cell
                # Optimization: separate the common conditions
                if nb_num == 0:  # No neighbors - spontaneous generation
                    grid_new[loc] = Alive()
                    # Update neighbor references
                    for n in nbhood[loc]:
                        live_nbrs_new[n].append(loc)
                        live_nbrs_num_new[n] += 1
                else:  # Settlement from neighbors
                    grid_new[loc] = settlement(loc, grid_old, live_nbrs_old, cost_func)
                    # Update neighbor references
                    nbrs = nbhood[loc]  # Cache neighborhood access
                    for n in nbrs:
                        live_nbrs_new[n].append(loc)
                        live_nbrs_num_new[n] += 1
                    events[loc] = 'settlement'
            else:  # Alive cell dies
                grid_new[loc] = empty_init
                # Update neighbor references
                nbrs = nbhood[loc]  # Cache neighborhood access
                for n in nbrs:
                    # This is a hot spot - optimize list removal
                    live_nbrs_new[n].remove(loc)
                    live_nbrs_num_new[n] -= 1

    return events