#!/usr/bin/env python

from __future__ import division

from math import exp
from string import ascii_letters
import random

# Setup curses for sane output
import curses
import curses.wrapper

# Model parameters
size = { 'x': 300, 'y': 300 }
init_dens = 0.0
init_stasis = { 0: frozenset([0,1,2,4,5,6,7,8]), 1: frozenset([2,3]) }
mut_prob = 0.02
exchange_prob = 0.01
vac_decay_prob = 0.01
unfit_cost = 0.8
neighborhood = 1

# Derived parameters
neighborhood_size = (2 * neighborhood + 1) * (2 * neighborhood + 1)

# Display parameters
disp_switch = 50
window = { 'x': 75, 'y': 15 }

def life():
    return { 'state': 1, 'stasis': init_stasis[1],
             'parent': random.choice(ascii_letters) }

def child(stasis, parent):
    return { 'state': 1, 'stasis': stasis, 'parent': parent }

vacuum = { 'state': 0, 'stasis': init_stasis[0] }

def decayed(stasis):
    return { 'state': 0, 'stasis': stasis }

def neighbors(loc):
    x, y = loc
    return [(nx % size['x'], ny % size['y'])
            for nx in range(x - neighborhood, x + neighborhood + 1)
            for ny in range(y - neighborhood, y + neighborhood + 1)
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
    genotypes = {}
    parents = {}
    life_lens = []
    vacuum_lens = []

    # Get current terminal dimensions
    term_y, term_x = stdscr.getmaxyx()
    
    def grid_push(y, x, s):
        try:
            grid_pad.addch(y, x, s)
        except curses.error:
            pass
        
    for x in range(size['x']):
        for y in range(size['y']):
            cell = grid[(x,y)]
            stasis = cell['stasis']
            stasis_len = len(stasis)
            if cell['state'] == 1:
                parent = cell['parent']
                parents.setdefault(parent, 0)
                parents[parent] += 1
                genotypes.setdefault(stasis, 0)
                genotypes[stasis] += 1
                life_lens.append(stasis_len)
                if disp_type == 'stasis':
                    if stasis_len > 9: grid_push(y, x, '+')
                    else: grid_push(y, x, str(stasis_len))
                elif disp_type == 'min':
                    if len(stasis) == 0: grid_push(y, x, 'x')
                    else:
                        stasis_min = min(stasis)
                        if stasis_min > 9: grid_push(y, x, '+')
                        else: grid_push(y, x, str(stasis_min))
                elif disp_type == 'max':
                    if len(stasis) == 0: grid_push(y, x, 'x')
                    else:
                        stasis_max = max(stasis)
                        if stasis_max > 9: grid_push(y, x, '+')
                        else: grid_push(y, x, str(stasis_max))
                elif disp_type == 'parent': grid_push(y, x, cell['parent'])
            else:
                vacuum_lens.append(stasis_len)
                grid_push(y, x, ' ')
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
    for s in range(neighborhood_size):
        if random.random() < mut_prob:
            diff.add(s)
    return child(settler_stasis.symmetric_difference(diff), parent)

def decay(stasis):
    lost = set([random.choice(list(stasis))])
    return decayed(stasis.difference(lost))

def exchange(old, live_nbrs, stasis, parent):
    if len(live_nbrs) == 0:
        exchanger_stasis = stasis
    else:
        exchanger_stasis = old[random.choice(live_nbrs)]['stasis']
    
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
    grid_new[loc] = vacuum
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

def do_sim(stdscr, max_gen = -1):
    # Setup curses display
    curses.curs_set(0)
    grid_pad = curses.newpad(size['y'], size['x'])
    stat_win = curses.newwin(0, 0, 0, 0)
    
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
                grid_0[loc] = vacuum

    generation = 0
    while True:
        if generation % 2 == 0:
            grid_old, live_nbrs_old = grid_0, live_nbrs_0
            grid_new, live_nbrs_new = grid_1, live_nbrs_1
        else:
            grid_old, live_nbrs_old = grid_1, live_nbrs_1
            grid_new, live_nbrs_new = grid_0, live_nbrs_0

        if generation % disp_switch == 0:
            disp = random.choice(['stasis', 'parent', 'max', 'min'])
        
        display(grid_old, generation, grid_pad, stat_win, stdscr,
                disp_type = disp)
        if generation == max_gen:
            break
        
        step(grid_old, grid_new, live_nbrs_old, live_nbrs_new, nbr_dict)
        generation += 1

curses.wrapper(do_sim)

