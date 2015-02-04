# Lif

Demonstration of a
[Conway's Game of Life](http://en.wikipedia.org/wiki/Conway%27s_Game_of_Life)
variant where the dynamics vary locally.

## Model

The standard Game of Life plays out on a square grid where each cell
is defined as adjacent to its 8-neighbors. Each cell has one of two
possible states: *alive* or *empty*. The dynamics are synchronous and
discrete. Living cells remain living if they have two or three living
neighbors. Empty cells remain empty unless they have three living
neighbors. Otherwise, the state flips.

Lif retains the synchronous discrete dynamics, grid topology, and
binary state of standard Life. However, in Lif, each state has
associated with it a *stasis set*, containing the number of living
neighbors that will not cause it to flip state. (The dynamics of
standard Life can be expressed like this with the stasis set for alive
cells of {2,3} and that for empty cells of {0,1,2,4,5,6,7,8}.) These
sets can vary individually for every cell. Biologically-inspired rules
describe how the stasis set of a newly-settled living cell is derived
from its possible parents. In the absence of parents, life may arise
[*de novo*](http://en.wikipedia.org/wiki/Spontaneous_generation). Other
biologically-inspired rules describe how an existing alive cell's
stasis set may be affected by those of its neighbors. Overcrowded
alive cells may become empty. The stasis sets of empty cells also
change over time, with a tendency to become increasingly habitable.

These processes are denoted *settlement*, *birth*, *exchange*,
*death*, and *gain of habitability* (suggestions for a better name
welcome).

## Requirements

* A reasonably modern copy of Python
* A terminal that can handle
  [curses](http://en.wikipedia.org/wiki/Curses_%28programming_library%29)
* Time that it will take for a horribly inefficient implementation to
  do its work
