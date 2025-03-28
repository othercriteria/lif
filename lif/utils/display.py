"""Display functions for Lif"""

import curses
from collections import defaultdict
from string import ascii_letters
from typing import Any, Dict, Optional, Tuple

from ..config import params
from ..grid import all_locs
from ..stasis import StasisKey, s_count, s_max, s_min, s_str
from .math import gini

# Type definitions
GridLocation = Tuple[int, int]
GridDict = Dict[GridLocation, Any]  # Will contain Alive or Empty objects

def display(
    grid: GridDict, 
    events: Dict[GridLocation, str], 
    generation: int, 
    grid_pad: Any, 
    stat_win: Any, 
    stdscr: Any, 
    disp: Dict[str, Any]
) -> Dict[str, Any]:
    """Display the grid and statistics"""
    stats = {'generation': generation}
    
    genotypes: Dict[str, int] = defaultdict(int)
    parents: Dict[int, int] = defaultdict(int)
    alive_sum, alive_n = 0, 0
    empty_sum, empty_n = 0, 0

    def draw(loc: GridLocation, s: str, p: Optional[int] = None) -> None:
        x, y = loc
        
        if s == ' ':
            grid_pad.addch(y, x, ' ')
        else:
            if loc not in events:
                emphasis = 0
            elif events[loc] == 'settlement':
                emphasis = curses.A_BOLD
            elif events[loc][0:8] == 'exchange':
                emphasis = curses.A_REVERSE

            if p is None:
                grid_pad.addch(y, x, s)
            else:
                attr = curses.color_pair(p % curses.COLORS)
                attr |= emphasis
                grid_pad.addch(y, x, s, attr)

    num_str = '0123456789'
    if disp['alive'] == 'stasis':
        def do_alive_disp(loc: GridLocation, s: StasisKey, p: int) -> None:
            draw(loc, num_str[s_count[s]], p)
    elif disp['alive'] == 'min':
        def do_alive_disp(loc: GridLocation, s: StasisKey, p: int) -> None:
            c = s_count[s]
            if c == 0:
                draw(loc, 'x', p)
            else:
                draw(loc, num_str[s_min[s]], p)
    elif disp['alive'] == 'max':
        def do_alive_disp(loc: GridLocation, s: StasisKey, p: int) -> None:
            c = s_count[s]
            if c == 0:
                draw(loc, 'x', p)
            else:
                draw(loc, num_str[s_max[s]], p)
    elif disp['alive'] == 'parent':
        def do_alive_disp(loc: GridLocation, s: StasisKey, p: int) -> None:
            parent_char = ascii_letters[p % 52]
            draw(loc, parent_char, p)
    
    if disp['empty']:
        def do_empty_disp(loc: GridLocation) -> None:
            draw(loc, ' ')
    else:
        def do_empty_disp(loc: GridLocation) -> None:
            pass

    for loc in all_locs():
        cell = grid[loc]
        stasis = cell.stasis
        stasis_len = s_count[stasis]
        if cell.alive:
            parent = cell.parent
            parents[parent] += 1
            genotypes[s_str[stasis]] += 1
            alive_sum += stasis_len
            alive_n += 1
            do_alive_disp(loc, stasis, parent)
        else:
            empty_sum += stasis_len
            do_empty_disp(loc)
        
    fitness = [(genotypes[g], g) for g in genotypes]
    fitness.sort(reverse=True, key=lambda p: p[0])
    offspring = [(parents[p], ascii_letters[p % 52]) for p in parents]
    offspring.sort(reverse=True)

    stats['species'] = len(offspring)
    # Convert to float for type compatibility
    stats['gini_species'] = float(gini(offspring))
    stats['gini_stasis'] = float(gini(fitness))
    
    # Get current terminal dimensions
    term_y, term_x = stdscr.getmaxyx()
    grid_pad.noutrefresh(0, 0, 0, 0, term_y - 9, term_x - 1)

    stat_win.erase()
    stat_win.resize(8, term_x - 1)
    stat_win.mvwin(term_y - 8, 0)
    rules = 'Lif/' + params['goh_m'][0:3]
    mode_line = f"{rules}\tDisp: {disp['alive']}\tExchange prob.: {params['exchange_r']:.2e}\tFit. cost: {params['fit_cost']:.2e}"
    stat_win.addstr(0, 0, mode_line)
    stat_win.addstr(1, 0, f"Population: {alive_n}")
    stats['alive'] = alive_n
    
    if alive_n > 0:
        alive_mean = alive_sum / alive_n
        stat_win.addstr(2, 0, f"Alive mean #(stasis): {alive_mean:.2f}")
        stats['alive_mean_stasis'] = float(alive_mean)
        
    from ..grid import num_locs
    empty_n = num_locs - alive_n
    if empty_n > 0:
        empty_mean = empty_sum / empty_n
        stat_win.addstr(3, 0, f"Empty mean #(stasis): {empty_mean:.2f}")
        stats['empty_mean_stasis'] = float(empty_mean)
        
    stat_win.addstr(5, 0, str(fitness)[0:term_x-1])
    stat_win.addstr(6, 0, str(offspring)[0:term_x-1])
    stat_win.addstr(7, 0, f"Generation: {generation}")
    stat_win.noutrefresh()

    curses.doupdate()

    return stats