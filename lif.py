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
params = { 'size': { 'x': 78, 'y': 17 },
           'init_stasis_p': 0.1,
           'mut_prob': 0.001,
           'exchange_prob': 0.01,
           'hab_prob': 1.0,
           'fit_cost': 5.0 }

def random_stasis(p):
    stasis = set()
    for s in range(9):
        if random.random() < p:
            stasis.add(s)
    return frozenset(stasis)

def alive():
    return { 'state': 1, 'stasis': random_stasis(params['init_stasis_p']),
             'parent': random.choice(ascii_letters) }

def child(stasis, parent):
    return { 'state': 1, 'stasis': stasis, 'parent': parent }

def empty():
    return { 'state': 0, 'stasis': frozenset(range(8)) }

def neighbors(loc):
    x, y = loc
    return [(nx % params['size']['x'], ny % params['size']['y'])
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

def display(grid, events, generation, grid_pad, stat_win, stdscr,
            disp_type = 'stasis'):
    genotypes = defaultdict(int)
    parents = defaultdict(int)
    alive_lens = []
    empty_lens = []

    # Get current terminal dimensions
    term_y, term_x = stdscr.getmaxyx()

    def draw(x, y, s, p = None):
        loc = (x,y)
        if not loc in events:
            emphasis = 0
        elif events[loc] == 'settlement':
            emphasis = curses.A_BOLD
        elif events[loc] == 'exchange':
            emphasis = curses.A_REVERSE
        
        try:
            if p == None:
                grid_pad.addch(y, x, s)
            else:
                attr = curses.color_pair(ord(p) % curses.COLORS)
                attr |= emphasis
                grid_pad.addch(y, x, s, attr)
        except curses.error:
            pass
        
    for x in range(params['size']['x']):
        for y in range(params['size']['y']):
            cell = grid[(x,y)]
            stasis = cell['stasis']
            stasis_len = len(stasis)
            if cell['state'] == 1:
                parent = cell['parent']
                parents[parent] += 1
                genotypes[stasis] += 1
                alive_lens.append(stasis_len)
                if disp_type == 'stasis':
                    draw(x, y, str(stasis_len), parent)
                elif disp_type == 'min':
                    if len(stasis) == 0: draw(x, y, 'x', parent)
                    else:
                        stasis_min = min(stasis)
                        draw(x, y, str(stasis_min), parent)
                elif disp_type == 'max':
                    if len(stasis) == 0: draw(x, y, 'x', parent)
                    else:
                        stasis_max = max(stasis)
                        draw(x, y, str(stasis_max), parent)
                elif disp_type == 'parent': draw(x, y, cell['parent'], parent)
            else:
                empty_lens.append(stasis_len)
                draw(x, y, ' ')
    grid_pad.noutrefresh(0, 0, 0, 0, term_y - 9, term_x - 1)
        
    fitness = [ (genotypes[g], list(g)) for g in genotypes ]
    fitness.sort(reverse = True)
    offspring = [ (parents[p], p) for p in parents ]
    offspring.sort(reverse = True)

    stat_win.erase()
    stat_win.resize(8, term_x - 1)
    stat_win.mvwin(term_y - 8, 0)
    mode_line = 'Display mode: %s\tExchange prob.: %.2e\tFit. cost: %.2e' % \
      (disp_type, params['exchange_prob'], params['fit_cost'])
    stat_win.addstr(0, 0, mode_line)
    num_alive = len(alive_lens)
    stat_win.addstr(1, 0, 'Population: %d' % num_alive)
    if num_alive > 0:
        mean_alive = sum(alive_lens) / num_alive
        stat_win.addstr(2, 0, 'Mean alive complexity: %.2f' % mean_alive)
    num_empty = len(empty_lens)
    if num_empty > 0:
        mean_empty = sum(empty_lens) / num_empty
        stat_win.addstr(3, 0, 'Mean empty habitability: %.2f' % mean_empty)
    stat_win.addstr(5, 0, str(fitness)[0:term_x-1])
    stat_win.addstr(6, 0, str(offspring)[0:term_x-1])
    stat_win.addstr(7, 0, 'Generation: %d' % generation)
    stat_win.noutrefresh()

    curses.doupdate()

def settlement(old, live_nbrs):
    probs = [exp(-params['fit_cost'] * len(old[n]['stasis']))
             for n in live_nbrs]
    settler = live_nbrs[weighted_choice(probs)]
    settler_stasis = old[settler]['stasis']
    parent = old[settler]['parent']
    diff = set()
    for s in range(9):
        if random.random() < params['mut_prob']:
            diff.add(s)
    return child(settler_stasis.symmetric_difference(diff), parent)

def gain_habitability(stasis):
    if len(stasis) > 0:
        lost = set([random.choice(list(stasis))])
        return { 'state': 0, 'stasis': stasis.difference(lost) }
    else:
        return { 'state': 0, 'stasis': stasis }

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

    # Stasis
    if num_live_nbrs in stasis:
        if state == 0:
            if random.random() < params['hab_prob']:
                grid_new[loc] = gain_habitability(stasis)
                return 'habitability'
            else:
                grid_new[loc] = cell
                return 'none'
        else:
            if random.random() < params['exchange_prob']:
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

    events = {}
    for loc in grid_old:
        change = step_cell(grid_old, grid_new, live_nbrs_old[loc], loc)
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

def do_sim(stdscr, grid_pad, stat_win):
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
        elif c == ord('r'):
            return 'restart'
        elif c == curses.KEY_DOWN:
            params['fit_cost'] *= 0.9
        elif c == curses.KEY_UP:
            params['fit_cost'] /= 0.9
        elif c == curses.KEY_LEFT:
            params['exchange_prob'] *= 0.9
        elif c == curses.KEY_RIGHT:
            params['exchange_prob'] /= 0.9
        
        if generation % 2 == 0:
            grid_old, live_nbrs_old = grid_0, live_nbrs_0
            grid_new, live_nbrs_new = grid_1, live_nbrs_1
        else:
            grid_old, live_nbrs_old = grid_1, live_nbrs_1
            grid_new, live_nbrs_new = grid_0, live_nbrs_0

        disp = { 0: 'stasis', 1: 'parent', 2: 'max', 3: 'min' }[mode]
        display(grid_old, events, generation, grid_pad, stat_win, stdscr, disp)
        
        events = step(grid_old, grid_new,
                      live_nbrs_old, live_nbrs_new, nbr_dict)
        generation += 1

def main(stdscr):
    # Setup curses display
    stdscr.nodelay(1)
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)
    grid_pad = curses.newpad(params['size']['y'], params['size']['x'])
    stat_win = curses.newwin(0, 0, 0, 0)

    while True:
        grid_pad.erase()
        stat_win.erase()
        
        r = do_sim(stdscr, grid_pad, stat_win)

        if r == 'quit':
            break
        
curses.wrapper(main)

