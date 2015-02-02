# Lif

Demonstration of a
[Conway's Game of Life](http://en.wikipedia.org/wiki/Conway%27s_Game_of_Life)
variant where the rules of the universe are dynamic. I need to dig
back into the code to understand what this entails, but here's the
gist. Being tolerant of a greater variety in number of neighbors
trades off with the ability to effectively settle neighboring
sites. Also, empty sites have a slow tendency towards [spontaneous generation](http://en.wikipedia.org/wiki/Spontaneous_generation).

## Model

The standard Game of Life plays out on a square grid where each cell
is defined as adjacent to its 8-neighbors. Each cell has one of two
possible states: alive or dead. The dynamics are synchronous and
discrete. Living cells remain living if they have two or three living
neighbors. Dead cells remain dead unless they have three living
neighbors. Otherwise, the state flips.

In Lif, each state has associated with it a *stasis* set,
containing the number of living neighbors that will not cause it to
flip state. For Life, the stasis set for all living cells is {2,3} and that
for all dead cells is {0,1,2,4,5,6,7,8}. In Lif, these sets can vary
individually for every cell. Biologically-inspired rules describe how
the stasis set of a newly-settled living cell is derived from its
possible parents, or arises *de novo$.

## Requirements

* A reasonably modern copy of Python
* A terminal that can handle
  [curses](http://en.wikipedia.org/wiki/Curses_%28programming_library%29)
* Time that it will take for a horribly inefficient implementation to
  do its work
