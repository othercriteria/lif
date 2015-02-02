#!/usr/bin/env python

from __future__ import division

from math import exp
from string import ascii_letters
from collections import defaultdict
import random

# Setup curses for sane output
import curses
import curses.wrapper

# Model parameters
size = { 'x': 78, 'y': 17 }
init_dens = 0.0
init_stasis_0_p = 0.9
init_stasis_1_p = 0.1
gof_prob = 0.01
exchange_prob = 0.01
vac_decay_prob = 0.05
unfit_cost = 5.0

def random_stasis(p):
    stasis = set()
    for s in range(9):
        if random.random() < p:
            stasis.add(s)
    return frozenset(stasis)

def life():
    return { 'state': 1, 'stasis': random_stasis(init_stasis_1_p),
             'parent': random.choice(ascii_letters) }

def child(stasis, parent):
    return { 'state': 1, 'stasis': stasis, 'parent': parent }

def vacuum():
    return { 'state': 0, 'stasis': random_stasis(init_stasis_0_p) }

def decayed(stasis):
    return { 'state': 0, 'stasis': stasis }

def neighbors(loc):
    x, y = loc
    return [(nx % size['x'], ny % size['y'])
            for nx in range(x - 1, x + 2)
            for ny in range(y - 1, y + 2)
            if not (nx == x and ny == y)]

# http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python
def weighted_choice(weights):
    rnd = random.random() * sum(weights)
    for i, w in enumerate(weights):
        rnd -= w
        if rnd < 0:
            return i

def display(grid, generation, grid_pad, stat_win, stdscr,
            disp_type = 'stasis'):
    genotypes = defaultdict(int)
    parents = defaultdict(int)
    life_lens = []
    vacuum_lens = []

    # Get current terminal dimensions
    term_y, term_x = stdscr.getmaxyx()

    def draw(y, x, s, p = None):
        try:
            if p == None:
                grid_pad.addch(y, x, s)
            else:
                color = ord(p) % curses.COLORS
                grid_pad.addch(y, x, s, curses.color_pair(color))
        except curses.error:
            pass
        
    for x in range(size['x']):
        for y in range(size['y']):
            cell = grid[(x,y)]
            stasis = cell['stasis']
            stasis_len = len(stasis)
            if cell['state'] == 1:
                parent = cell['parent']
                parents[parent] += 1
                genotypes[stasis] += 1
                life_lens.append(stasis_len)
                if disp_type == 'stasis':
                    if stasis_len > 9: draw(y, x, '+', parent)
                    else: draw(y, x, str(stasis_len), parent)
                elif disp_type == 'min':
                    if len(stasis) == 0: draw(y, x, 'x', parent)
                    else:
                        stasis_min = min(stasis)
                        if stasis_min > 9: draw(y, x, '+', parent)
                        else: draw(y, x, str(stasis_min), parent)
                elif disp_type == 'max':
                    if len(stasis) == 0: draw(y, x, 'x', parent)
                    else:
                        stasis_max = max(stasis)
                        if stasis_max > 9: draw(y, x, '+', parent)
                        else: draw(y, x, str(stasis_max), parent)
                elif disp_type == 'parent': draw(y, x, cell['parent'], parent)
            else:
                vacuum_lens.append(stasis_len)
                draw(y, x, ' ')
    grid_pad.noutrefresh(0, 0, 0, 0, term_y - 9, term_x - 1)
        
    fitness = [ (genotypes[g], list(g)) for g in genotypes ]
    fitness.sort(reverse = True)
    offspring = [ (parents[p], p) for p in parents ]
    offspring.sort(reverse = True)

    stat_win.erase()
    stat_win.resize(8, term_x - 1)
    stat_win.mvwin(term_y - 8, 0)
    stat_win.addstr(0, 0, 'Mode: %s' % disp_type)
    num_life = len(life_lens)
    stat_win.addstr(1, 4, 'Population: %d' % num_life)
    if num_life > 0:
        mean_life = sum(life_lens) / num_life
        stat_win.addstr(2, 4, 'Mean life: %.2f' % mean_life)
    num_vacuum = len(vacuum_lens)
    if num_vacuum > 0:
        mean_vacuum = sum(vacuum_lens) / num_vacuum
        stat_win.addstr(3, 4, 'Mean vacuum: %.2f' % mean_vacuum)
    stat_win.addstr(5, 0, str(fitness)[0:term_x-1])
    stat_win.addstr(6, 0, str(offspring)[0:term_x-1])
    stat_win.addstr(7, 0, 'Generation: %d' % generation)
    stat_win.noutrefresh()

    curses.doupdate()

def settlement(old, live_nbrs):
    probs = [exp(-unfit_cost * len(old[n]['stasis'])) for n in live_nbrs]
    settler = live_nbrs[weighted_choice(probs)]
    settler_stasis = old[settler]['stasis']
    parent = old[settler]['parent']
    diff = set()
    for s in range(9):
        if random.random() < gof_prob:
            diff.add(s)
    return child(settler_stasis.symmetric_difference(diff), parent)

def decay(stasis):
    lost = set([random.choice(list(stasis))])
    return decayed(stasis.difference(lost))

def exchange(old, live_nbrs, stasis, parent):
    if len(live_nbrs) == 0:
        exchanger_stasis = stasis
    else:
        conspecific_nbrs = [live_nbr for live_nbr in live_nbrs
                            if old[live_nbr]['parent'] == parent]
        if len(conspecific_nbrs) == 0:
            exchanger_stasis = old[random.choice(live_nbrs)]['stasis']
        else:
            exchanger_stasis = old[random.choice(conspecific_nbrs)]['stasis']
    
    new_stasis = set()
    new_stasis.update(stasis.intersection(exchanger_stasis))
    for s in stasis.symmetric_difference(exchanger_stasis):
        if random.random() < 0.5:
            new_stasis.add(s)
    return child(frozenset(new_stasis), parent)

def step_cell(grid_old, grid_new, live_nbrs_old, loc):
    cell = grid_old[loc]
    state = cell['state']
    stasis = cell['stasis']
    num_live_nbrs = len(live_nbrs_old)
    
    if num_live_nbrs in stasis:
        if state == 0:
            if random.random() < vac_decay_prob and len(stasis) > 1:
                # Vacuum decay
                grid_new[loc] = decay(stasis)
            else:
                grid_new[loc] = cell
        else:
            if random.random() < exchange_prob:
                # Exchange
                grid_new[loc] = exchange(grid_old, live_nbrs_old,
                                         stasis, cell['parent'])
            else:
                grid_new[loc] = cell
        return 'none'

    if state == 0:
        if num_live_nbrs == 0:
            # De novo birth
            grid_new[loc] = life()
        else:
            # Settlement
            grid_new[loc] = settlement(grid_old, live_nbrs_old)
        return 'birth'

    # Overcrowding
    grid_new[loc] = vacuum()
    return 'death'

def step(grid_old, grid_new, live_nbrs_old, live_nbrs_new, nbr_dict):
    for loc in live_nbrs_old:
        live_nbrs_new[loc] = live_nbrs_old[loc][:]

    for loc in grid_old:
        change = step_cell(grid_old, grid_new, live_nbrs_old[loc], loc)
        if change == 'none': continue
        if change == 'birth':
            for n in nbr_dict[loc]:
                live_nbrs_new[n].append(loc)
        elif change == 'death':
            for n in nbr_dict[loc]:
                live_nbrs_new[n].remove(loc)

def do_sim(stdscr, grid_pad, stat_win):
    grid_0 = {}
    grid_1 = {}
    live_nbrs_0 = {}
    live_nbrs_1 = {}
    nbr_dict = {}
    for x in range(size['x']):
        for y in range(size['y']):
            loc = (x,y)
            nbrs = neighbors(loc)
            nbr_dict[loc] = nbrs
            live_nbrs_0.setdefault(loc, [])
            if random.random() < init_dens:
                grid_0[loc] = life()
                for n in nbrs:
                    live_nbrs_0.setdefault(n, []).append(loc)
            else:
                grid_0[loc] = vacuum()

    generation = 0
    mode = 0
    while True:
        # Handle use input
        c = stdscr.getch()
        if c == ord('q'):
            return 'quit'
        elif c == ord(' '):
            mode = (mode + 1) % 4
        elif c == ord('r'):
            return 'restart'
        
        if generation % 2 == 0:
            grid_old, live_nbrs_old = grid_0, live_nbrs_0
            grid_new, live_nbrs_new = grid_1, live_nbrs_1
        else:
            grid_old, live_nbrs_old = grid_1, live_nbrs_1
            grid_new, live_nbrs_new = grid_0, live_nbrs_0

        disp = { 0: 'stasis', 1: 'parent', 2: 'max', 3: 'min' }[mode]
        display(grid_old, generation, grid_pad, stat_win, stdscr, disp)
        
        step(grid_old, grid_new, live_nbrs_old, live_nbrs_new, nbr_dict)
        generation += 1

def main(stdscr):
    # Setup curses display
    stdscr.nodelay(1)
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)
    grid_pad = curses.newpad(size['y'], size['x'])
    stat_win = curses.newwin(0, 0, 0, 0)

    while True:
        grid_pad.erase()
        stat_win.erase()
        
        r = do_sim(stdscr, grid_pad, stat_win)

        if r == 'quit':
            break
        
curses.wrapper(main)

