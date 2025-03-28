#!/usr/bin/env python
"""
Deep optimization analysis for Lif with extended simulation runs
"""

import sys
import os
import time
import random
import cProfile
import pstats
import argparse
import traceback
from io import StringIO
from typing import Dict, List, Tuple, Any, Optional, Set

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from lif
from lif.config import params, update_params
from lif.grid import step, initialize_grid
from lif.models import Alive, Empty, empty_init

# Import numba if available
try:
    import numba
    from numba import njit, jit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    print("Numba not available - using native Python implementation")

# Performance tracking
PROFILING_STATS = {}

def run_long_simulation(generations: int = 300, grid_size: Tuple[int, int] = (50, 50)) -> Dict[str, Any]:
    """
    Run a longer simulation to get realistic performance data
    Returns timing data and statistics
    """
    start_time = time.time()
    
    try:
        # Setup grid parameters
        params['size']['x'] = grid_size[0]
        params['size']['y'] = grid_size[1]
        # Ensure we have default values even if they were changed
        params['alive_p'] = 0.1
        params['mut_p'] = 0.0001
        params['exchange_r'] = 0.001
        params['goh_r'] = 1.0
        params['goh_m'] = 'max'
        params['fit_cost'] = 5.0
        params['toroidal'] = True
        
        initialize_grid()
        
        # Initialize grid and neighbors
        grid = {}
        live_nbrs = {}
        live_nbrs_num = {}
    
        from lif.grid import all_locs, neighborhood
        for loc in all_locs():
            live_nbrs[loc] = []
            live_nbrs_num[loc] = 0
            grid[loc] = Empty()
    
        # Add some random initial alive cells
        num_initial = int(grid_size[0] * grid_size[1] * 0.1)  # 10% of cells start alive
        all_locs_list = list(grid.keys())
        for _ in range(num_initial):
            loc = random.choice(all_locs_list)
            grid[loc] = Alive()
            # Update neighbor counts
            for n in neighborhood[loc]:
                live_nbrs[n].append(loc)
                live_nbrs_num[n] += 1
        
        # Store stats by generation
        stats = {
            'alive_count': [],
            'step_times': [],
            'events': [],
        }
        
        # Run simulation
        for gen in range(generations):
            gen_start = time.time()
            
            # Create new data structures for next step
            grid_new = {}
            live_nbrs_new = {}
            live_nbrs_num_new = {}
            
            for loc in live_nbrs:
                live_nbrs_new[loc] = live_nbrs[loc][:]
                live_nbrs_num_new[loc] = live_nbrs_num[loc]
            
            # Perform a step
            events = step(
                grid, grid_new,
                live_nbrs, live_nbrs_new,
                live_nbrs_num, live_nbrs_num_new
            )
            
            # Update for next generation
            grid = grid_new
            live_nbrs = live_nbrs_new
            live_nbrs_num = live_nbrs_num_new
            
            # Record stats
            gen_time = time.time() - gen_start
            alive_count = sum(1 for cell in grid.values() if cell.alive)
            
            stats['step_times'].append(gen_time)
            stats['alive_count'].append(alive_count)
            stats['events'].append(len(events))
            
            # Progress indicator
            if gen % 50 == 0:
                print(f"Generation {gen}/{generations} - Alive: {alive_count} - Step time: {gen_time:.4f}s")
        
        # Calculate overall stats
        total_time = time.time() - start_time
        stats['total_time'] = total_time
        stats['avg_step_time'] = sum(stats['step_times']) / len(stats['step_times'])
        stats['generations'] = generations
        
        return stats
        
    except Exception as e:
        print(f"Error in simulation: {e}")
        traceback.print_exc()
        return {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'total_time': time.time() - start_time,
            'generations': 0
        }

def optimize_step_function():
    """
    Create more optimized versions of the step function
    Returns a dictionary of optimized functions and their descriptions
    """
    optimized_funcs = {}
    
    # Store original function
    from lif.grid import step as original_step
    optimized_funcs['original'] = (original_step, "Original implementation")
    
    # Implement data structure optimization
    # This version uses arrays and optimized data structures for better cache locality
    def step_optimized_ds(
        grid_old, grid_new,
        live_nbrs_old, live_nbrs_new,
        live_nbrs_num_old, live_nbrs_num_new
    ):
        """Optimized version with better data structures"""
        from lif.config import params
        from math import exp
        from lif.models import Alive, Empty, empty_init
        from lif.grid import neighborhood
        from lif.utils.math import runif, weighted_choice
        
        # Determine active gain of habitability mechanism
        if params['goh_m'] == 'max':
            from lif.stasis import s_lose_max
            def goh(cell):
                return Empty(s_lose_max[cell.stasis])
        elif params['goh_m'] == 'min':
            from lif.stasis import s_lose_min
            def goh(cell):
                return Empty(s_lose_min[cell.stasis])
        else:  # 'random'
            from lif.stasis import s_list, s_lose
            import random
            def goh(cell):
                pick = random.choice(s_list[cell.stasis])
                return Empty(s_lose[cell.stasis][pick])
        
        # Precompute cost function
        cost_func = {}
        f = params['fit_cost']
        for s in range(10):
            cost_func[s] = exp(-f * s)
        
        events = {}
        goh_r = params['goh_r']
        exchange_r = params['exchange_r']
        
        # Pre-sort grid cells by type for better branch prediction
        alive_cells = []
        empty_cells = []
        
        for loc, cell in grid_old.items():
            if cell.alive:
                alive_cells.append((loc, cell))
            else:
                empty_cells.append((loc, cell))
                
        # Make sure we have safe neighbor counts
        for loc in grid_old:
            nb_num = live_nbrs_num_old[loc]
            if nb_num >= len(grid_old[loc].stasis):
                live_nbrs_num_old[loc] = len(grid_old[loc].stasis) - 1
        
        # Process alive cells
        for loc, cell in alive_cells:
            nb_num = live_nbrs_num_old[loc]
            
            if cell.stasis[nb_num]:  # Stasis
                if nb_num == 0 or runif() >= exchange_r:  # No change
                    grid_new[loc] = cell
                else:  # Exchange
                    from lif.grid import exchange
                    new, conspecific = exchange(loc, grid_old, live_nbrs_old)
                    grid_new[loc] = new
                    events[loc] = 'exchange conspecific' if conspecific else 'exchange interspecific'
            else:  # Death
                grid_new[loc] = empty_init
                for n in neighborhood[loc]:
                    live_nbrs_new[n].remove(loc)
                    live_nbrs_num_new[n] -= 1
        
        # Process empty cells
        for loc, cell in empty_cells:
            nb_num = live_nbrs_num_old[loc]
            
            if cell.stasis[nb_num]:  # Stasis
                grid_new[loc] = goh(cell) if runif() < goh_r else cell
            else:  # Birth
                if nb_num == 0:  # Spontaneous generation
                    grid_new[loc] = Alive()
                    for n in neighborhood[loc]:
                        live_nbrs_new[n].append(loc)
                        live_nbrs_num_new[n] += 1
                else:  # Settlement
                    from lif.grid import settlement
                    grid_new[loc] = settlement(loc, grid_old, live_nbrs_old, cost_func)
                    for n in neighborhood[loc]:
                        live_nbrs_new[n].append(loc)
                        live_nbrs_num_new[n] += 1
                    events[loc] = 'settlement'
        
        return events
    
    optimized_funcs['optimized_ds'] = (step_optimized_ds, "Optimized data structures")
    
    return optimized_funcs

def run_comparison(generations: int = 300, grid_size: Tuple[int, int] = (50, 50)) -> Dict[str, Dict[str, Any]]:
    """
    Compare different optimization strategies over long simulation runs
    Returns dictionary of results for each strategy
    """
    # Get optimized functions
    optimized_funcs = optimize_step_function()
    
    results = {}
    
    # Run with original implementation as baseline
    print("\n== Testing Original Implementation ==")
    orig_func_name, orig_func_desc = "original", "Original implementation"
    orig_func = optimized_funcs[orig_func_name][0]
    
    # Backup and replace step function
    from lif import grid
    original_step = grid.step
    grid.step = orig_func
    
    # Run and measure
    orig_stats = run_long_simulation(generations, grid_size)
    results[orig_func_name] = {
        'description': orig_func_desc,
        'stats': orig_stats,
    }
    
    # Restore original step
    grid.step = original_step
    
    # Run with optimized implementations
    for name, (func, desc) in optimized_funcs.items():
        if name == 'original':
            continue  # Already tested
            
        print(f"\n== Testing {desc} ==")
        
        # Replace step function
        grid.step = func
        
        # Run and measure
        opt_stats = run_long_simulation(generations, grid_size)
        results[name] = {
            'description': desc,
            'stats': opt_stats,
        }
        
        # Calculate speedup
        baseline_time = results['original']['stats']['total_time']
        speedup = baseline_time / opt_stats['total_time']
        results[name]['speedup'] = speedup
        
        print(f"Speedup: {speedup:.2f}x")
    
    # Restore original step
    grid.step = original_step
    
    return results

def profile_simulation(generations: int = 100, grid_size: Tuple[int, int] = (50, 50)) -> str:
    """Run profiling on the simulation to identify bottlenecks"""
    # Setup params
    params['size']['x'] = grid_size[0]
    params['size']['y'] = grid_size[1]
    initialize_grid()
    
    # Run via profiler
    pr = cProfile.Profile()
    pr.enable()
    run_long_simulation(generations, grid_size)
    pr.disable()
    
    # Format and return results
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumtime')
    ps.print_stats(30)  # Top 30 functions by cumulative time
    return s.getvalue()

def analyze_memory_usage(generations: int = 100, grid_size: Tuple[int, int] = (50, 50)) -> Dict[str, Any]:
    """Analyze memory usage patterns of the simulation"""
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_stats = {
            'before': process.memory_info().rss / 1024 / 1024,  # MB
            'generation_samples': [],
            'after': None,
        }
        
        # Setup params
        params['size']['x'] = grid_size[0]
        params['size']['y'] = grid_size[1]
        initialize_grid()
        
        # Run simulation and track memory usage
        stats = run_long_simulation(generations, grid_size)
        
        # Record final memory usage
        memory_stats['after'] = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"\nMemory usage analysis:")
        print(f"Starting memory: {memory_stats['before']:.2f} MB")
        print(f"Ending memory: {memory_stats['after']:.2f} MB")
        print(f"Difference: {memory_stats['after'] - memory_stats['before']:.2f} MB")
        
        return memory_stats
    except ImportError:
        print("psutil not available - memory analysis skipped")
        return {}

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Deep optimization analysis for Lif")
    parser.add_argument('-g', '--generations', type=int, default=300,
                       help='Number of generations to simulate (default: 300)')
    parser.add_argument('-s', '--size', type=int, default=50,
                       help='Grid size (default: 50x50)')
    parser.add_argument('-p', '--profile', action='store_true',
                       help='Run profiling on the simulation')
    parser.add_argument('-m', '--memory', action='store_true',
                       help='Analyze memory usage patterns')
    parser.add_argument('-c', '--compare', action='store_true',
                       help='Compare optimization strategies')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Fix random seed for reproducibility
    random.seed(42)
    
    # Safety check for stasis values
    from lif.stasis import stasis_all
    print(f"Checking stasis structure: stasis_all length = {len(stasis_all)}")
    
    generations = args.generations
    grid_size = (args.size, args.size)
    
    print(f"Running analysis with {generations} generations on {grid_size[0]}x{grid_size[1]} grid")
    
    if args.profile:
        print("\nRunning profiling...")
        profiling_results = profile_simulation(generations // 3, grid_size)  # Use fewer generations for profiling
        print(profiling_results)
    
    if args.memory:
        print("\nAnalyzing memory usage...")
        memory_results = analyze_memory_usage(generations // 3, grid_size)  # Use fewer generations for memory analysis
    
    if args.compare:
        print("\nComparing optimization strategies...")
        comparison_results = run_comparison(generations, grid_size)
        
        # Print summary table
        print("\n== Optimization Results Summary ==")
        print(f"{'Strategy':<20} {'Total Time':<12} {'Avg Step Time':<15} {'Speedup':<10}")
        print("-" * 60)
        
        baseline_time = comparison_results['original']['stats']['total_time']
        for name, result in comparison_results.items():
            time = result['stats']['total_time']
            avg_time = result['stats']['avg_step_time']
            speedup = baseline_time / time if name != 'original' else 1.0
            print(f"{name:<20} {time:<12.2f}s {avg_time:<15.6f}s {speedup:<10.2f}x")
    
    # If no specific analysis was requested, run a basic simulation
    if not (args.profile or args.memory or args.compare):
        print("\nRunning basic simulation...")
        stats = run_long_simulation(generations, grid_size)
        
        print("\n== Simulation Results ==")
        print(f"Total time: {stats['total_time']:.2f}s")
        if 'avg_step_time' in stats:
            print(f"Average step time: {stats['avg_step_time']:.6f}s")
        if 'alive_count' in stats and stats['alive_count']:
            print(f"Final alive count: {stats['alive_count'][-1]}")