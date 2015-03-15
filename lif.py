#!/usr/bin/env python

from __future__ import division

from math import exp
from string import ascii_letters
from collections import defaultdict, namedtuple
from itertools import product
import random
from random import random as runif
import argparse
import csv

# Setup curses for sane output
import curses

# Model parameters
params = { 'size': { 'x': 80, 'y': 80 },
           'toroidal': True,
           'standard': False,
           'alive_p': 0.1,
           'mut_p': 0.0001,
           'exchange_r': 0.001,
           'goh_r': 1.0,
           'goh_m': 'max',
           'fit_cost': 5.0,
           'outfile': 'lif_stats.csv' }

# Precompute stasis operations
ks = product([False,True], repeat = 9)
s_str = {}
s_count = {}
s_list = {}
s_set = {}
s_min = {}
s_max = {}
s_gain = {}
s_lose = {}
s_lose_min = {}
s_lose_max = {}
for k in ks:
    count = sum(k)
    as_list = [i for i in range(9) if k[i]]
    as_set = {i for i in range(9) if k[i]}

    s_count[k] = sum(k)
    s_str[k] = str(as_set)
    s_list[k] = as_list
    s_set[k] = as_set

    s_gain[k] = {}
    for v in range(9):
        k_l = list(k)
        k_l[v] = True
        s_gain[k][v] = tuple(k_l)

    s_lose[k] = {}
    for v in range(9):
        k_l = list(k)
        k_l[v] = False
        s_lose[k][v] = tuple(k_l)

    if count > 0:
        s_min[k] = min(as_list)
        s_max[k] = max(as_list)
        s_lose_min[k] = s_lose[k][s_min[k]]
        s_lose_max[k] = s_lose[k][s_max[k]]

stasis_none = tuple([False] * 9)
stasis_all = tuple([True] * 9)

def set_to_stasis(s):
    l = len(s)
    if l == 9:
        return stasis_all
    elif l == 0:
        return stasis_none
    else:
        arr = [False] * 9
        for i in s:
            arr[i] = True
        return tuple(arr)

class Empty():
    alive = False
    
    def __init__(self, stasis = None):
        if not stasis:
            self.stasis = stasis_all
        else:
            self.stasis = stasis
empty_init = Empty()
                    
class Alive():
    alive = True
    
    def __init__(self, blank = False):
        if not blank:
            global parent_counter
            parent_counter += 1
            self.parent = parent_counter
            self.stasis = set_to_stasis(iid_set(params['alive_p']))

    def child(self, new_stasis):
        new = Alive(blank = True)
        new.parent = self.parent
        new.stasis = new_stasis
        return new

def iid_set(p):
    return { s for s in range(9) if runif() < p }

# http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python
def weighted_choice(weights):
    rnd = runif() * sum(weights)
    for i, w in enumerate(weights):
        rnd -= w
        if rnd < 0:
            return i

def display(grid, events, generation, grid_pad, stat_win, stdscr, disp):
    stats = { 'generation': generation }
    
    genotypes = defaultdict(int)
    parents = defaultdict(int)
    alive_sum, alive_n = 0, 0
    empty_sum, empty_n = 0, 0

    def draw(loc, s, p = None):
        x, y = loc
        
        if s == ' ':
            grid_pad.addch(y, x, ' ')
        else:
            if not loc in events:
                emphasis = 0
            elif events[loc] == 'settlement':
                emphasis = curses.A_BOLD
            elif events[loc][0:8] == 'exchange':
                emphasis = curses.A_REVERSE

            if p == None:
                grid_pad.addch(y, x, s)
            else:
                attr = curses.color_pair(p % curses.COLORS)
                attr |= emphasis
                grid_pad.addch(y, x, s, attr)

    num_str = '0123456789'
    if disp['alive'] == 'stasis':
        def do_alive_disp(loc, s, p):
            draw(loc, num_str[s_count[s]], p)
    elif disp['alive'] == 'min':
        def do_alive_disp(loc, s, p):
            c = s_count[s]
            if c == 0:
                draw(loc, 'x', p)
            else:
                draw(loc, num_str[s_min[s]], p)
    elif disp['alive'] == 'max':
        def do_alive_disp(loc, s, p):
            c = s_count[s]
            if c == 0:
                draw(loc, 'x', p)
            else:
                draw(loc, num_str[s_max[s]], p)
    elif disp['alive'] == 'parent':
        def do_alive_disp(loc, s, p):
            parent_char = ascii_letters[p % 52]
            draw(loc, parent_char, p)
    if disp['empty']:
        def do_empty_disp(loc):
            draw(loc, ' ')
    else:
        def do_empty_disp(loc):
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
        
    fitness = [ (genotypes[g], g) for g in genotypes ]
    fitness.sort(reverse = True, key = lambda p: p[0])
    offspring = [ (parents[p], ascii_letters[p % 52]) for p in parents ]
    offspring.sort(reverse = True)

    stats['species'] = len(offspring)

    # See http://en.wikipedia.org/wiki/Gini_coefficient for formula
    def gini(ys):
        n = len(ys)
        sy, siy = 0, 0
        if n > 0:
            for i, y in enumerate(sorted(ys, key = lambda p: p[0])):
                sy += y[0]
                siy += y[0] * (i+1)
            return 2 * siy / (n * sy) - (n + 1) / n
        else:
            return None
    stats['gini_species'] = gini(offspring)
    stats['gini_stasis'] = gini(fitness)
    
    # Get current terminal dimensions
    term_y, term_x = stdscr.getmaxyx()
    grid_pad.noutrefresh(0, 0, 0, 0, term_y - 9, term_x - 1)

    stat_win.erase()
    stat_win.resize(8, term_x - 1)
    stat_win.mvwin(term_y - 8, 0)
    rules = 'Lif/' + params['goh_m'][0:3]
    mode_line = '%s\tDisp: %s\tExchange prob.: %.2e\tFit. cost: %.2e' % \
      (rules, disp['alive'], params['exchange_r'], params['fit_cost'])
    stat_win.addstr(0, 0, mode_line)
    stat_win.addstr(1, 0, 'Population: %d' % alive_n)
    stats['alive'] = alive_n
    if alive_n > 0:
        alive_mean = alive_sum / alive_n
        stat_win.addstr(2, 0, 'Alive mean #(stasis): %.2f' % alive_mean)
        stats['alive_mean_stasis'] = alive_mean
    empty_n = num_locs - alive_n
    if empty_n > 0:
        empty_mean = empty_sum / empty_n
        stat_win.addstr(3, 0, 'Empty mean #(stasis): %.2f' % empty_mean)
        stats['empty_mean_stasis'] = empty_mean
    stat_win.addstr(5, 0, str(fitness)[0:term_x-1])
    stat_win.addstr(6, 0, str(offspring)[0:term_x-1])
    stat_win.addstr(7, 0, 'Generation: %d' % generation)
    stat_win.noutrefresh()

    curses.doupdate()

    return stats

def mutate(parent):
    mut = iid_set(params['mut_p'])
    if sum(mut) > 0:
        new_stasis_mut = s_set[parent.stasis].symmetric_difference(mut)
        return parent.child(set_to_stasis(new_stasis_mut))
    else:
        return parent

def settlement(loc, grid_old, live_nbrs_old, cost_func):
    probs = [cost_func[s_count[grid_old[n].stasis]]
             for n in live_nbrs_old[loc]]
    settler = grid_old[live_nbrs_old[loc][weighted_choice(probs)]]

    return mutate(settler)

def exchange(loc, grid_old, live_nbrs_old):
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

def step(grid_old, grid_new, live_nbrs_old, live_nbrs_new,
         live_nbrs_num_old, live_nbrs_num_new):
    # Determine active gain of habitability mechanism
    if params['goh_m'] == 'max':
        def goh(cell):
            return Empty(s_lose_max[cell.stasis])
    elif params['goh_m'] == 'min':
        def goh(cell):
            return Empty(s_lose_min[cell.stasis])
    elif params['goh_m'] == 'random':
        def goh(cell):
            pick = random.choice(s_list[cell.stasis])
            return Empty(s_lose[cell.stasis][pick])

    # Precompute cost function for settlement
    cost_func = {}
    f = params['fit_cost']
    for s in range(10):
        cost_func[s] = exp(-f * s)
        
    events = {}
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

def do_sim(stdscr, grid_pad, stat_win, outwriter):
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
        if generation == args.blind:
            break

        if not args.blind:
            # Handle use input
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

            disp_alive = { 0: 'stasis', 1: 'parent', 2: 'max', 3: 'min' }[mode]
            disp = { 'alive': disp_alive, 'empty': disp_empty }
            statrow = display(grid, events, generation,
                              grid_pad, stat_win, stdscr, disp)

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

parent_counter = 0
def main(stdscr):
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

# Update parameters with command line arguments
parser = argparse.ArgumentParser(description = 'Game of Life variant.')
parser.add_argument('width', metavar = 'x', type = int, nargs = '?',
                    default = params['size']['x'],
                    help = 'Grid width (default: %(default)s)')
parser.add_argument('height', metavar = 'y', type = int, nargs = '?',
                    default = params['size']['y'],
                    help = 'Grid height (default: %(default)s)')
parser.add_argument('-alive_p', metavar = 'p', type = float,
                    default = params['alive_p'],
                    help = 'Alive stasis bit prob. (default: %(default)s)')
parser.add_argument('-mut_p', metavar = 'p', type = float,
                    default = params['mut_p'],
                    help = 'Mutation bit prob. (default: %(default)s)')
parser.add_argument('-exchange_r', metavar = 'r', type = float,
                    default = params['exchange_r'],
                    help = 'Exchange rate (default: %(default)s)')
parser.add_argument('-goh_r', metavar = 'r', type = float,
                    default = params['goh_r'],
                    help = 'Gain of habitability rate (default: %(default)s)')
parser.add_argument('-pick', metavar = 'mode', type = str,
                    default = params['goh_m'],
                    help = 'Habitability gain pick (default: %(default)s)')
parser.add_argument('-fit_cost', metavar = 'c', type = float,
                    default = params['fit_cost'],
                    help = 'Fitness cost (default: %(default)s)')
parser.add_argument('-nontoroidal', action = 'store_true',
                    help = 'Use nontoroidal topology')
parser.add_argument('-output', metavar = 'FILE', type = str,
                    default = params['outfile'],
                    help = 'Output file for run stats (default: %(default)s)')
parser.add_argument('-timing', action='store_true',
                    help = 'Run with Python profiling.')
parser.add_argument('-blind', metavar = 'g', type = int,
                    help = 'Profile without IO, terminate at set generation.')
args = parser.parse_args()
if args.blind:
    args.timing = True
params['size']['x'] = args.width
params['size']['y'] = args.height
params['alive_p'] = args.alive_p
params['mut_p'] = args.mut_p
params['exchange_r'] = args.exchange_r
params['goh_r'] = args.goh_r
params['goh_m'] = args.pick
params['fit_cost'] = args.fit_cost
params['toroidal'] = not args.nontoroidal
params['outfile'] = args.output

def all_locs():
    return ((x,y)
            for x in range(params['size']['x'])
            for y in range(params['size']['y']))

# Generate valid grid locations
valid_locs = set(all_locs())
num_locs = len(valid_locs)

def neighbors(loc):
    x, y = loc

    if params['toroidal']:
        candidates = ((nx % params['size']['x'], ny % params['size']['y'])
                      for nx in range(x - 1, x + 2)
                      for ny in range(y - 1, y + 2)
                      if not (nx == x and ny == y))
    else:
        candidates = ((nx, ny)
                      for nx in range(x - 1, x + 2)
                      for ny in range(y - 1, y + 2)
                      if not (nx == x and ny == y))

    return tuple(c for c in candidates if c in valid_locs)

# Generate neighborhoods
neighborhood = {}
for loc in all_locs():
    neighborhood[loc] = neighbors(loc)

if args.timing:
    import cProfile

    # For consistent simulation outcome
    random.seed(137)

    if args.blind:
        cProfile.run('do_sim(None, None, None, None)')
    else:
        cProfile.run('curses.wrapper(main)')
else:
    curses.wrapper(main)
