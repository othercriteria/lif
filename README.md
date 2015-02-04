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
welcome) and are sketched out below. We can alternatively think of the
stasis set as a bit vector of length 9.
* Settlement or birth: If an empty cell has a number of living
  neighbors not in its stasis set, it becomes alive. If this number of
  neighbors is 0, it forms a new lineage having a stasis set with each
  bit on with independent probability `init_stasis_p`. If the number
  of neighbors is not 0, one of the neighbors will become its parent
  with probability proportional to exp(-`fit_cost` * #(parent stasis
  set)). It will inherit this parent's stasis set with each bit
  flipped with independent probability `mut_prob`.
* Exchange: A living cell with living neighbors experiences this with
  probability `exchange_prob`. A random neighbor is picked
  uniformly. If any of the neighbors is of the same lineage, the
  selection is only from among these conspecifics. The living cell
  takes as its new stasis set the consensus of its old stasis set and
  that of its neighbor, where disagreement is resolved with
  independent probability 0.5. This is followed by mutation, as in
  settlement.
* Death: A new empty cell comes into existence with stasis set
  {0,1,2,3,4,5,6,7,8}.
* Gain of habitability: An empty cell experiences this with
  probability `hab_prob`. A randomly chosen 1 in the stasis set is
  flipped to 0.

## Demonstration

Running the script in the console as `./lif.py` (having made it
executable with `chmod u+x lif.py` if necessary) starts a visual
demonstration of this model. Modifying model parameters requires
making edits to the script. In addition to those described above,
`size` determines the dimensions of the cell grid on which the
demonstration runs.

Controls:
* q: Quits program.
* r: Restarts simulation.
* space: Cycles through display modes for living cells.
  * "stasis": Length of cell's stasis set.
  * "parent": Cell's parent.
  * "max": Maximum value in cell's stasis set, "x" if stasis set is
    empty.
  * "min": Minimum value in cell's stasis set, "x" if stasis set is
    empty.
* left/right: Lower or raise `exchange_prob`.
* down/up: Lower or raise `fit_cost`.
* s: Toggle between Lif and standard Life dynamics.

## Requirements

* A reasonably modern copy of Python
* A terminal that can handle
  [curses](http://en.wikipedia.org/wiki/Curses_%28programming_library%29)
* Time that it will take for a horribly inefficient implementation to
  do its work
