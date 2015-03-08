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

class Stasis:
    def __init__(self, iter = None):
        self.contents = [False] * 9
        self._count = 0
        if iter:
            for i in iter:
                self.contents[i] = True
                self._count += 1

    def copy(self):
        new = Stasis()
        new.contents[:] = self.contents
        new._count = self._count
        return new
            
    def list(self):
        return [i for i in range(9) if self.contents[i]]

    def set(self):
        return { i for i in range(9) if self.contents[i] }

    def askey(self):
        return self.set().__str__()
            
    def gain(self, v):
        self.contents[v] = True
        self._count += 1

    def lose(self, v):
        self.contents[v] = False
        self._count -= 1

    def count(self):
        return self._count

    def contains(self, v):
        return self.contents[v]

    def min(self):
        for i in range(0, 9):
            if self.contents[i]:
                return i
        # Should never reach here
            
    def max(self):
        for i in range(8, -1, -1):
            if self.contents[i]:
                return i
        # Should never reach here
                
def random_stasis(p):
    stasis = Stasis()
    for s in range(9):
        if random.random() < p:
            stasis.gain(s)
    return stasis

def alive():
    global parent_counter
    parent_counter += 1
    return { 'state': 1, 'stasis': random_stasis(params['alive_p']),
             'parent': parent_counter }

def child(stasis, parent):
    return { 'state': 1, 'stasis': stasis, 'parent': parent }

def empty():
    return { 'state': 0, 'stasis': Stasis(range(8)) }

def neighbors(loc):
    x, y = loc
    if params['toroidal']:
        return [(nx % params['size']['x'], ny % params['size']['y'])
                for nx in range(x - 1, x + 2)
                for ny in range(y - 1, y + 2)
                if not (nx == x and ny == y)]
    else:
        return [(nx, ny)
                for nx in range(x - 1, x + 2)
                for ny in range(y - 1, y + 2)
                if 0 <= nx < params['size']['x']
                if 0 <= ny < params['size']['y']]

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

def settlement(old, live_nbrs):
    probs = [exp(-params['fit_cost'] * old[n]['stasis'].count())
             for n in live_nbrs]
    settler = live_nbrs[weighted_choice(probs)]
    settler_stasis = old[settler]['stasis']
    parent = old[settler]['parent']

    new_stasis = settler_stasis.set()
    diff = { s for s in range(9) if random.random() < params['mut_p'] }
    new_stasis_mut = new_stasis.symmetric_difference(diff)
    return child(Stasis(new_stasis_mut), parent)

def exchange(grid, live_nbrs, stasis, parent):
    conspecific_nbrs = [live_nbr for live_nbr in live_nbrs
                        if grid[live_nbr]['parent'] == parent]
    if len(conspecific_nbrs) == 0:
        exchanger_stasis = grid[random.choice(live_nbrs)]['stasis']
    else:
        exchanger_stasis = grid[random.choice(conspecific_nbrs)]['stasis']
    
    p1, p2 = stasis.set(), exchanger_stasis.set()
    new_stasis = p1.intersection(p2)
    for s in p1.symmetric_difference(p2):
        if random.random() < 0.5:
            new_stasis.add(s)
    diff = { s for s in range(9) if random.random() < params['mut_p'] }
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

def step(grid_old, grid_new, live_nbrs_old, live_nbrs_new, nbr_dict):
    for loc in live_nbrs_old:
        live_nbrs_new[loc] = live_nbrs_old[loc][:]

    # Determine active gain of habitability mechanism
    if params['goh_m'] == 'max':
        def goh_stasis(stasis):
            stasis.lose(stasis.max())
    elif params['goh_m'] == 'min':
        def goh_stasis(stasis):
            stasis.lose(stasis.min())
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
            for n in nbr_dict[loc]:
                live_nbrs_new[n].remove(loc)
        elif change == 'settlement':
            for n in nbr_dict[loc]:
                live_nbrs_new[n].append(loc)
            events[loc] = 'settlement'
        elif change == 'exchange':
            events[loc] = 'exchange'
        elif change == 'birth':
            for n in nbr_dict[loc]:
                live_nbrs_new[n].append(loc)

    return events

def do_sim(stdscr, grid_pad, stat_win, outwriter):
    grid_0 = {}
    grid_1 = {}
    live_nbrs_0 = {}
    live_nbrs_1 = {}
    nbr_dict = {}
    for x in range(params['size']['x']):
        for y in range(params['size']['y']):
            loc = (x,y)
            nbrs = neighbors(loc)
            nbr_dict[loc] = nbrs
            live_nbrs_0.setdefault(loc, [])
            if random.random() < 0:
                grid_0[loc] = alive()
                for n in nbrs:
                    live_nbrs_0.setdefault(n, []).append(loc)
            else:
                grid_0[loc] = empty()

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
        
        if generation % 2 == 0:
            grid_old, live_nbrs_old = grid_0, live_nbrs_0
            grid_new, live_nbrs_new = grid_1, live_nbrs_1
        else:
            grid_old, live_nbrs_old = grid_1, live_nbrs_1
            grid_new, live_nbrs_new = grid_0, live_nbrs_0

        disp = { 0: 'stasis', 1: 'parent', 2: 'max', 3: 'min' }[mode]
        statrow = display(grid_old, events, generation,
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
        
        events = step(grid_old, grid_new,
                      live_nbrs_old, live_nbrs_new, nbr_dict)
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
