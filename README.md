# lif

Demonstration of a
[Conway's Game of Life](http://en.wikipedia.org/wiki/Conway%27s_Game_of_Life)
variant where the rules of the universe are dynamic. I need to dig
back into the code to understand what this entails, but here's the
gist. Being tolerant of a greater variety in number of neighbors
trades off with the ability to effectively settle neighboring
sites. Also, empty sites have a slow tendency towards [spontaneous generation](http://en.wikipedia.org/wiki/Spontaneous_generation).

## Requirements

* A reasonably modern copy of Python
* A terminal that can handle
  [curses](http://en.wikipedia.org/wiki/Curses_%28programming_library%29)
* Time that it will take for a horribly inefficient implementation to
  do its work
