#!/usr/bin/env python

from __future__ import division

from math import exp
from string import ascii_letters
from collections import defaultdict
import random
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
from itertools import product
ks = product([False,True], repeat=9)
d_count = {}
d_list = {}
d_set = {}
d_min = {}
d_max = {}
d_gain = {}
d_lose = {}
d_lose_min = {}
d_lose_max = {}
for k in ks:
    count = sum(k)
    as_list = [i for i in range(9) if k[i]]
    as_set = {i for i in range(9) if k[i]}

    d_count[k] = sum(k)
    d_list[k] = as_list
    d_set[k] = as_set

    d_gain[k] = {}
    for v in range(9):
        k_l = list(k)
        k_l[v] = True
        d_gain[k][v] = tuple(k_l)

    d_lose[k] = {}
    for v in range(9):
        k_l = list(k)
        k_l[v] = False
        d_lose[k][v] = tuple(k_l)

    if count > 0:
        d_min[k] = min(as_list)
        d_max[k] = max(as_list)
        d_lose_min[k] = d_lose[k][d_min[k]]
        d_lose_max[k] = d_lose[k][d_max[k]]

stasis_none = tuple([False] * 9)
stasis_all = tuple([True] * 9)
class Stasis:
    def __init__(self, iter = None, init_empty = False):
        if init_empty:
            self._contents = stasis_all
        elif iter:
            arr = [False] * 9
            for i in iter:
                arr[i] = True
            self._contents = tuple(arr)
        else:
            self._contents = stasis_none

    def copy(self):
        new = Stasis()
        new._contents = self._contents
        return new

    def list(self):
        return d_list[self._contents].copy()

    def set(self):
        return d_set[self._contents].copy()

    def askey(self):
        return self.set().__str__()
            
    def gain(self, v):
        self._contents = d_gain[self._contents][v]

    def lose(self, v):
        self._contents = d_lose[self._contents][v]

    def count(self):
        return d_count[self._contents]

    def contains(self, v):
        return self._contents[v]

    def min(self):
        return d_min[self._contents]
            
    def max(self):
        return d_max[self._contents]

    def lose_min(self):
        self._contents = d_lose_min[self._contents]

    def lose_max(self):
        self._contents = d_lose_max[self._contents]
     
def iid_set(p):
    return { s for s in range(9) if random.random() < p }
                        
def alive():
    global parent_counter
    parent_counter += 1
    return { 'state': 1, 'stasis': Stasis(iid_set(params['alive_p'])),
             'parent': parent_counter }

def child(stasis, parent):
    return { 'state': 1, 'stasis': stasis, 'parent': parent }

def empty():
    return { 'state': 0, 'stasis': Stasis(init_empty = True) }

def neighbors(loc):
    x, y = loc
    if params['toroidal']:
        return tuple([(nx % params['size']['x'], ny % params['size']['y'])
                    for nx in range(x - 1, x + 2)
                    for ny in range(y - 1, y + 2)
                    if not (nx == x and ny == y)])
    else:
        return tuple([(nx, ny)
                    for nx in range(x - 1, x + 2)
                    for ny in range(y - 1, y + 2)
                    if 0 <= nx < params['size']['x']
                    if 0 <= ny < params['size']['y']])

# http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python
def weighted_choice(weights):
    rnd = random.random() * sum(weights)
    for i, w in enumerate(weights):
        rnd -= w
        if rnd < 0:
            return i

def display(grid, events, generation, grid_pad, stat_win, stdscr,
            disp_type = 'stasis'):
    stats = { 'generation': generation }
    
    genotypes = defaultdict(int)
    parents = defaultdict(int)
    alive_lens = []
    empty_lens = []

    def draw(x, y, s, p = None):
        loc = (x,y)
        if not loc in events:
            emphasis = 0
        elif events[loc] == 'settlement':
            emphasis = curses.A_BOLD
        elif events[loc] == 'exchange':
            emphasis = curses.A_REVERSE
        
        if p == None:
            grid_pad.addch(y, x, s)
        else:
            attr = curses.color_pair(p % curses.COLORS)
            attr |= emphasis
            grid_pad.addch(y, x, s, attr)

    if disp_type == 'stasis':
        def do_alive_disp(x, y, s, p):
            draw(x, y, str(s.count()), p)
    elif disp_type == 'min':
        def do_alive_disp(x, y, s, p):
            c = s.count()
            if c == 0:
                draw(x, y, 'x', p)
            else:
                draw(x, y, str(s.min()))
    elif disp_type == 'max':
        def do_alive_disp(x, y, s, p):
            c = s.count()
            if c == 0:
                draw(x, y, 'x', p)
            else:
                draw(x, y, str(s.max()))
    elif disp_type == 'parent':
        def do_alive_disp(x, y, s, p):
            parent_char = ascii_letters[p % 52]
            draw(x, y, parent_char, p)
                    
    for x in range(params['size']['x']):
        for y in range(params['size']['y']):
            cell = grid[(x,y)]
            stasis = cell['stasis']
            stasis_len = stasis.count()
            if cell['state'] == 1:
                parent = cell['parent']
                parents[parent] += 1
                genotypes[stasis.askey()] += 1
                alive_lens.append(stasis_len)
                do_alive_disp(x, y, stasis, parent)
            else:
                empty_lens.append(stasis_len)
                draw(x, y, ' ')
        
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
      (rules, disp_type, params['exchange_r'], params['fit_cost'])
    stat_win.addstr(0, 0, mode_line)
    num_alive = len(alive_lens)
    stat_win.addstr(1, 0, 'Population: %d' % num_alive)
    stats['alive'] = num_alive
    if num_alive > 0:
        mean_alive = sum(alive_lens) / num_alive
        stat_win.addstr(2, 0, 'Alive mean #(stasis): %.2f' % mean_alive)
        stats['mean_alive_stasis'] = mean_alive
    num_empty = len(empty_lens)
    if num_empty > 0:
        mean_empty = sum(empty_lens) / num_empty
        stat_win.addstr(3, 0, 'Empty mean #(stasis): %.2f' % mean_empty)
        stats['mean_empty_stasis'] = mean_empty
    stat_win.addstr(5, 0, str(fitness)[0:term_x-1])
    stat_win.addstr(6, 0, str(offspring)[0:term_x-1])
    stat_win.addstr(7, 0, 'Generation: %d' % generation)
    stat_win.noutrefresh()

    curses.doupdate()

    return stats

def settlement(grid_old, live_nbrs_old):
    probs = [exp(-params['fit_cost'] * grid_old[n]['stasis'].count())
             for n in live_nbrs_old]
    settler = live_nbrs_old[weighted_choice(probs)]
    settler_stasis = grid_old[settler]['stasis']
    parent = grid_old[settler]['parent']

    new_stasis = settler_stasis.set()
    diff = iid_set(params['mut_p'])
    new_stasis_mut = new_stasis.symmetric_difference(diff)
    return child(Stasis(new_stasis_mut), parent)

def exchange(grid_old, live_nbrs_old, stasis, parent):
    conspecific_nbrs = [live_nbr for live_nbr in live_nbrs_old
                        if grid_old[live_nbr]['parent'] == parent]
    if len(conspecific_nbrs) == 0:
        exchanger_stasis = grid_old[random.choice(live_nbrs_old)]['stasis']
    else:
        exchanger_stasis = grid_old[random.choice(conspecific_nbrs)]['stasis']
    
    p1, p2 = stasis.set(), exchanger_stasis.set()
    new_stasis = p1.intersection(p2)
    for s in p1.symmetric_difference(p2):
        if random.random() < 0.5:
            new_stasis.add(s)
    diff = iid_set(params['mut_p'])
    new_stasis_mut = new_stasis.symmetric_difference(diff)
    return child(Stasis(new_stasis_mut), parent)

def gain_of_heritability(stasis, goh_stasis):
    new_stasis = stasis.copy()
    goh_stasis(new_stasis)
    return { 'state': 0, 'stasis': new_stasis }

def step_cell(grid_old, grid_new, live_nbrs_old, loc, goh_stasis):
    cell = grid_old[loc]
    state = cell['state']
    stasis = cell['stasis']
    num_live_nbrs = len(live_nbrs_old)

    # Stasis
    if stasis.contains(num_live_nbrs):
        if state == 0:
            if random.random() < params['goh_r']:
                if stasis.count() == 0:
                    grid_new[loc] = cell
                    return 'none'
                grid_new[loc] = gain_of_heritability(stasis, goh_stasis)
                return 'habitability'
            else:
                grid_new[loc] = cell
                return 'none'
        else:
            if num_live_nbrs > 0 and random.random() < params['exchange_r']:
                grid_new[loc] = exchange(grid_old, live_nbrs_old,
                                         stasis, cell['parent'])
                return 'exchange'
            else:
                grid_new[loc] = cell
                return 'none'

    # Gain
    if state == 0:
        if num_live_nbrs == 0:
            grid_new[loc] = alive()
            return 'birth'
        else:
            grid_new[loc] = settlement(grid_old, live_nbrs_old)
            return 'settlement'

    # Loss
    grid_new[loc] = empty()
    return 'death'

def step(grid_old, grid_new, live_nbrs_old, live_nbrs_new, neighborhood):
    # Determine active gain of habitability mechanism
    if params['goh_m'] == 'max':
        def goh_stasis(stasis):
            stasis.lose_max()
    elif params['goh_m'] == 'min':
        def goh_stasis(stasis):
            stasis.lose_min()
    elif params['goh_m'] == 'random':
        def goh_stasis(stasis):
            pick = random.choice(stasis.list())
            stasis.lose(pick)
        
    events = {}
    for loc in grid_old:
        change = step_cell(grid_old, grid_new, live_nbrs_old[loc], loc,
                           goh_stasis)
        if change == 'none' or change == 'habitability': continue
        elif change == 'death':
            for n in neighborhood[loc]:
                live_nbrs_new[n].remove(loc)
        elif change == 'settlement':
            for n in neighborhood[loc]:
                live_nbrs_new[n].append(loc)
            events[loc] = 'settlement'
        elif change == 'exchange':
            events[loc] = 'exchange'
        elif change == 'birth':
            for n in neighborhood[loc]:
                live_nbrs_new[n].append(loc)

    return events

def do_sim(stdscr, grid_pad, stat_win, outwriter):
    # Initialize grid, neighborhoods, and alive neighbor pointers
    grid = {}
    neighborhood = {}
    live_nbrs = {}
    for x in range(params['size']['x']):
        for y in range(params['size']['y']):
            loc = (x,y)
            nbrs = neighbors(loc)
            neighborhood[loc] = nbrs
            live_nbrs.setdefault(loc, [])
            grid[loc] = empty()

    generation = 0
    mode = 0
    events = {}
    while True:
        # Handle use input
        c = stdscr.getch()
        if c == ord('q'):
            return 'quit'
        elif c == ord(' '):
            mode = (mode + 1) % 4
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
        
        disp = { 0: 'stasis', 1: 'parent', 2: 'max', 3: 'min' }[mode]
        statrow = display(grid, events, generation,
                          grid_pad, stat_win, stdscr, disp)

        settlements = 0
        exchanges = 0
        for k in events:
            if events[k] == 'settlement':
                settlements += 1
            elif events[k] == 'exchange':
                exchanges += 1
        statrow['settlements'] = settlements
        statrow['exchanges'] = exchanges
        outwriter.writerow(statrow)

        grid_new = {}
        live_nbrs_new = {}
        for loc in live_nbrs:
            live_nbrs_new[loc] = live_nbrs[loc][:]
        events = step(grid, grid_new, live_nbrs, live_nbrs_new, neighborhood)
        grid = grid_new
        live_nbrs = live_nbrs_new
        
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
    fieldnames = ['generation', 'settlements', 'exchanges',
                  'alive', 'species',
                  'mean_alive_stasis', 'mean_empty_stasis',
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
                    help = 'Output file for run statis (default: %(default)s)')
parser.add_argument('-timing', action='store_true',
                    help = 'Run with Python profiling.')
args = parser.parse_args()
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

if args.timing:
    import cProfile
    cProfile.run('curses.wrapper(main)')
else:
    curses.wrapper(main)
