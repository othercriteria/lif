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

# Generate valid grid locations
valid_locs: Set[GridLocation] = set(all_locs())
num_locs: int = len(valid_locs)

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

# Generate neighborhoods
neighborhood: Neighborhood = {}
for loc in all_locs():
    neighborhood[loc] = neighbors(loc)

def settlement(
    loc: GridLocation,
    grid_old: Grid,
    live_nbrs_old: Dict[GridLocation, List[GridLocation]],
    cost_func: Dict[int, float]
) -> Alive:
    """Create a new settlement from neighboring cells"""
    probs = [cost_func[s_count[grid_old[n].stasis]]
             for n in live_nbrs_old[loc]]
    settler = grid_old[live_nbrs_old[loc][weighted_choice(probs)]]

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
    cost_func = {}
    f = params['fit_cost']
    for s in range(10):
        cost_func[s] = exp(-f * s)
        
    events: Dict[GridLocation, str] = {}
    for loc in grid_old:
        cell = grid_old[loc]

        # Stasis
        if cell.stasis[live_nbrs_num_old[loc]]:
            if not cell.alive:
                if runif() < params['goh_r']:
                    grid_new[loc] = goh(cell)
                else:
                    grid_new[loc] = cell
            else:
                if (live_nbrs_num_old[loc] > 0 and
                    runif() < params['exchange_r']):
                    new, conspecific = exchange(loc, grid_old, live_nbrs_old)
                    grid_new[loc] = new
                    if conspecific:
                        events[loc] = 'exchange conspecific'
                    else:
                        events[loc] = 'exchange interspecific'
                else:
                    grid_new[loc] = cell
        else:
            # Gain
            if not cell.alive:
                if live_nbrs_num_old[loc] == 0:
                    grid_new[loc] = Alive()
                    for n in neighborhood[loc]:
                        live_nbrs_new[n].append(loc)
                        live_nbrs_num_new[n] += 1
                else:
                    grid_new[loc] = settlement(loc, grid_old,
                                             live_nbrs_old, cost_func)
                    for n in neighborhood[loc]:
                        live_nbrs_new[n].append(loc)
                        live_nbrs_num_new[n] += 1
                    events[loc] = 'settlement'
            else:
                # Loss
                grid_new[loc] = empty_init
                for n in neighborhood[loc]:
                    live_nbrs_new[n].remove(loc)
                    live_nbrs_num_new[n] -= 1

    return events