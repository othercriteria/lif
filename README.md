# Lif

Demonstration of a [Conway's Game of Life](http://en.wikipedia.org/wiki/Conway%27s_Game_of_Life) variant where the dynamics vary locally.

For an informal, blog-y treatment, see my post [I want more Life](http://mesokurtosis.com/posts/2015-02-19-lif.html).

## Model

The standard Game of Life plays out on a square grid where each cell is defined as adjacent to its 8-neighbors. Each cell has one of two possible states: *alive* or *empty*. The dynamics are synchronous and discrete. Living cells remain living if they have two or three living neighbors. Empty cells remain empty unless they have three living neighbors. Otherwise, the state flips.

Lif retains the synchronous discrete dynamics, grid topology, and binary state of standard Life. However, in Lif, each state has associated with it a *stasis set*, containing the number of living neighbors that will not cause it to flip state. (The dynamics of standard Life can be expressed like this with the stasis set for alive cells of {2,3} and that for empty cells of {0,1,2,4,5,6,7,8}.) These sets can vary individually for every cell. Biologically-inspired rules describe how the stasis set of a newly-settled living cell is derived from its possible parents. In the absence of parents, life may arise [*de novo*](http://en.wikipedia.org/wiki/Spontaneous_generation). Other biologically-inspired rules describe how an existing alive cell's stasis set may be affected by those of its neighbors. Overcrowded alive cells may become empty. The stasis sets of empty cells also change over time, with a tendency to become increasingly habitable.

These processes are denoted *settlement*, *birth*, *exchange*, *death*, and *gain of habitability* (suggestions for a better name welcome) and are sketched out below. We can switch into thinking of the stasis set as a bit vector of length 9 when convenient.
* Settlement or birth: If an empty cell has a number of living neighbors not in its stasis set, it becomes alive. If this number of neighbors is 0, it forms a new lineage having a stasis set with each bit on with independent probability `alive_p`. If the number of neighbors is not 0, one of the neighbors will become its parent with probability proportional to exp(-`fit_cost` * #(parent stasis set)). It will inherit this parent's stasis set with each bit flipped with independent probability `mut_p`.
* Exchange: A living cell with living neighbors experiences this with probability `exchange_r`. A random neighbor is picked uniformly. If any of the neighbors is of the same lineage, the selection is only from among these conspecifics. The living cell takes as its new stasis set the consensus of its old stasis set and that of its neighbor, where disagreement is resolved with independent probability 0.5. This is followed by mutation, as in settlement.
* Death: A new empty cell comes into existence with stasis set {0,1,2,3,4,5,6,7,8}.
* Gain of habitability: An empty cell experiences this with probability `goh_r`. A chosen 1 in the stasis set is flipped to 0. Depending on the mode `goh_m`, the largest (`max`), the smallest (`min`), or a random element (`random`) is chosen.

In the absence of an infinite gird, I default to a toroidal (wrap-around) topology. This can be turned off using the `toroidal` parameter but the non-uniformity is annoying.

## Installation

To install the program, navigate to a destination directory and then run the standard sequence of commands:

```
git clone https://github.com/othercriteria/lif.git
cd lif/
./setup.py install
```

For development with optimizations:

```
nix develop
```

## Usage

Once installed, running the command `lif.py` in the console starts a visual demonstration of this model. All model parameters can be specified as command line arguments (see `lif.py -h` for details).

```
python lif.py [width] [height] [options]
```

Options:
- `-h`: Show help message
- `-alive_p p`: Alive stasis bit probability (default: 0.1)
- `-mut_p p`: Mutation bit probability (default: 0.0001)
- `-exchange_r r`: Exchange rate (default: 0.001)
- `-goh_r r`: Gain of habitability rate (default: 1.0)
- `-pick mode`: Habitability gain pick mode (default: 'max')
- `-fit_cost c`: Fitness cost (default: 5.0)
- `-nontoroidal`: Use nontoroidal topology
- `-output FILE`: Output file for run stats (default: 'lif_stats.csv')
- `-timing`: Run with Python profiling
- `-blind g`: Profile without IO, terminate at set generation
- `-generations g`: Terminate simulation after specified number of generations

The first two positional arguments set the grid width and height. If the terminal is too small to display the entire grid, only the top-left corner will be seen but the dynamics are not affected. Particularly for the `max` gain of habitability mode, a grid size of at least 80 × 80 is suggested to avoid triviality. Keep in mind, though, that the computation time for a generation scales roughly with the number of grid cells.

### Controls

* q: Quits program.
* r: Restarts simulation.
* space: Cycles through display modes for living cells.
  * "stasis": Length of cell's stasis set.
  * "parent": Cell's parent.
  * "max": Maximum value in cell's stasis set, "x" if stasis set is empty.
  * "min": Minimum value in cell's stasis set, "x" if stasis set is empty.
* p: Toggle erasing alive sites after death.
* left/right: Lower or raise `exchange_prob`.
* down/up: Lower or raise `fit_cost`.
* 1-3: Set gain of habitability mode.

## Optimized Version

For better performance, run with optimizations enabled:

```
python lif_optimized.py [width] [height] [options] -opt
```

Additional options:
- `-opt`: Use optimized implementations where available
- `--use-numba`: Prefer Numba optimizations if available
- `--use-cython`: Prefer Cython optimizations if available

## Performance Analysis

Run performance benchmarks and optimization analysis:

```
make benchmark         # Run basic benchmarks
make optimize          # Build Cython optimized modules
make deep-optimize     # Run extended optimization comparison
make profile           # Profile the simulation to identify bottlenecks
```

## Testing and Development

```
make test             # Run tests
make lint             # Check linting with ruff
make typecheck        # Check types with mypy
make format           # Format code with ruff
make clean            # Clean build artifacts
```

## Requirements

* Python 3.8+ (updated for Python 3.12 compatibility)
* For optimizations: Numba, Cython, NumPy (optional)
* A terminal that can handle [curses](http://en.wikipedia.org/wiki/Curses_%28programming_library%29)

## License

MIT License