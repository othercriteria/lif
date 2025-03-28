"""Core simulation code for Lif"""

from typing import Dict, List, Set, Tuple, Any, Optional
import curses
import csv
import random
import cProfile

from .config import params
from .models import empty_init
from .grid import all_locs, step
from .utils.display import display

# Will be set by cli.py
args = None

def do_sim(
    stdscr: Optional[Any],
    grid_pad: Optional[Any],
    stat_win: Optional[Any],
    outwriter: Optional[Any]
) -> str:
    """Run the simulation"""
    # Initialize grid, neighborhoods, and alive neighbor pointers
    grid = {}
    live_nbrs = {}
    live_nbrs_num = {}
    for loc in all_locs():
        live_nbrs[loc] = []
        live_nbrs_num[loc] = 0
        grid[loc] = empty_init

    generation = 0
    mode = 0
    disp_empty = True
    events = {}
    while True:
        if args and hasattr(args, 'blind') and generation == args.blind:
            break

        if not args or (hasattr(args, 'blind') and not args.blind) and stdscr is not None:
            # Handle user input
            c = stdscr.getch()
            if c == ord('q'):
                return 'quit'
            elif c == ord(' '):
                mode = (mode + 1) % 4
            elif c == ord('p'):
                disp_empty = not disp_empty
            elif c == ord('3'):
                params['goh_m'] = 'max'
            elif c == ord('1'):
                params['goh_m'] = 'min'
            elif c == ord('2'):
                params['goh_m'] = 'random'
            elif c == ord('r'):
                return 'restart'
            elif c == curses.KEY_DOWN:
                params['fit_cost'] *= 0.9
            elif c == curses.KEY_UP:
                params['fit_cost'] /= 0.9
            elif c == curses.KEY_LEFT:
                params['exchange_r'] *= 0.9
            elif c == curses.KEY_RIGHT:
                params['exchange_r'] /= 0.9

            disp_alive = {0: 'stasis', 1: 'parent', 2: 'max', 3: 'min'}[mode]
            disp = {'alive': disp_alive, 'empty': disp_empty}
            statrow = display(grid, events, generation,
                            grid_pad, stat_win, stdscr, disp)

            if outwriter is not None:
                settlements = 0
                exchanges_conspecific = 0
                exchanges_interspecific = 0
                for k in events:
                    if events[k] == 'settlement':
                        settlements += 1
                    elif events[k] == 'exchange conspecific':
                        exchanges_conspecific += 1
                    elif events[k] == 'exchange interspecific':
                        exchanges_interspecific += 1
                statrow['settlements'] = settlements
                statrow['exchanges_conspecific'] = exchanges_conspecific
                statrow['exchanges_interspecific'] = exchanges_interspecific
                outwriter.writerow(statrow)

        grid_new = {}
        live_nbrs_new = {}
        live_nbrs_num_new = {}
        for loc in live_nbrs:
            live_nbrs_new[loc] = live_nbrs[loc][:]
            live_nbrs_num_new[loc] = live_nbrs_num[loc]
        events = step(grid, grid_new, live_nbrs, live_nbrs_new,
                    live_nbrs_num, live_nbrs_num_new)
        grid = grid_new
        live_nbrs = live_nbrs_new
        live_nbrs_num = live_nbrs_num_new
        
        generation += 1
    
    return "completed"

def main(stdscr: Any = None) -> None:
    """Main function to setup and run the simulation"""
    if stdscr is None:
        return
        
    # Setup curses display
    stdscr.nodelay(1)
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)
    grid_pad = curses.newpad(params['size']['y'], params['size']['x']+1)
    stat_win = curses.newwin(0, 0, 0, 0)

    # Setup output file
    outfile = open(params['outfile'], 'w')
    fieldnames = ['generation', 'settlements',
                'exchanges_conspecific', 'exchanges_interspecific',
                'alive', 'species',
                'alive_mean_stasis', 'empty_mean_stasis',
                'gini_species', 'gini_stasis']
    outwriter = csv.DictWriter(outfile, fieldnames=fieldnames)
    outwriter.writeheader()
    
    while True:
        grid_pad.erase()
        stat_win.erase()
        
        r = do_sim(stdscr, grid_pad, stat_win, outwriter)

        if r == 'quit':
            break