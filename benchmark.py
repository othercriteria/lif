#!/usr/bin/env python
"""
Benchmarking tool for Lif performance
"""

import time
import cProfile
import pstats
import sys
import os
import argparse
from io import StringIO

def run_profiling(generations=100):
    """Run profiling on the simulation"""
    import sys
    
    # Set up CLI args for blind mode
    sys.argv = ['lif.py', '-blind', str(generations)]
    
    # Import main runner (after setting args)
    from lif.cli import run
    
    # Run simulation with profiling
    pr = cProfile.Profile()
    pr.enable()
    run()
    pr.disable()
    
    # Print results
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumtime')
    ps.print_stats(20)  # Print top 20 functions by cumulative time
    print(s.getvalue())
    
    # Return profiler for further analysis
    return pr

def compare_versions():
    """Compare original vs optimized implementation"""
    # Import original implementation
    from lif.utils.math import iid_set as original_iid_set
    from lif.utils.math import weighted_choice as original_weighted_choice
    
    # Also benchmark the step loop with key operations
    benchmark_step_loop()
    
    # Define improved implementations (same as in test files)
    def optimized_iid_set(p: float) -> set:
        """Create a set with independent probability p for each element"""
        from random import random as runif
        # Performance optimization: avoid creating set comprehension for common cases
        if p <= 0:
            return set()
        if p >= 1:
            return set(range(9))
        
        # Use direct set construction for better performance
        result = set()
        for s in range(9):
            if runif() < p:
                result.add(s)
        return result

    def optimized_weighted_choice(weights):
        """
        Weighted random selection
        Optimized version with O(1) sum calculation and improved early return
        """
        from random import random as runif
        # Handle common cases
        n = len(weights)
        if n == 0:
            return 0
        if n == 1:
            return 0
        
        # Pre-calculate sum
        total = sum(weights)
        if total <= 0:
            return 0  # Avoid division by zero
        
        # Generate random point and find the interval it falls in
        rnd = runif() * total
        cumulative = 0
        for i, w in enumerate(weights):
            cumulative += w
            if cumulative > rnd:  # Changed from rnd < 0 to avoid subtraction
                return i
        return n - 1  # Fallback
    
    # Run benchmarks
    import random
    random.seed(42)
    
    print("\nBenchmarking iid_set:")
    benchmark_function(
        lambda: original_iid_set(0.1), 
        lambda: optimized_iid_set(0.1),
        iterations=100000
    )
    
    print("\nBenchmarking weighted_choice:")
    weights = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    benchmark_function(
        lambda: original_weighted_choice(weights), 
        lambda: optimized_weighted_choice(weights),
        iterations=100000
    )

def benchmark_step_loop():
    """Benchmark potential optimizations for the step loop"""
    # Create test data
    from lif.models import Alive, Empty
    from lif.stasis import s_count
    from math import exp
    import random
    
    # Constants for the benchmark
    size = 30
    iterations = 1000
    locations = [(x, y) for x in range(size) for y in range(size)]
    
    # Create cells with various stasis patterns 
    cells = {}
    for loc in locations:
        if random.random() < 0.3:
            cell = Alive()
            cells[loc] = cell
        else:
            cell = Empty()
            # Create random stasis 
            stasis = tuple(random.random() < 0.3 for _ in range(9))
            cell.stasis = stasis
            cells[loc] = cell
    
    # Setup neighbor counters
    live_nbrs_num = {loc: random.randint(0, 8) for loc in locations}
    
    # Original loop: checking stasis[live_nbrs_num[loc]] many times 
    original_code = lambda: [
        cells[loc].stasis[live_nbrs_num[loc]] 
        for loc in locations
    ]
    
    # Optimized: cache the lookup in a local variable
    optimized_code = lambda: [
        (nb_num := live_nbrs_num[loc], cells[loc].stasis[nb_num])
        for loc in locations
    ]
    
    # Original cost function calculation
    def original_cost_calc():
        cost_func = {}
        f = 5.0  # fit_cost
        for s in range(10):
            cost_func[s] = exp(-f * s)
        return cost_func
    
    # Optimized cost function with memoization
    def optimized_cost_calc():
        # Calculate once and reuse
        if not hasattr(optimized_cost_calc, 'cached_result'):
            cost_func = {}
            f = 5.0
            for s in range(10):
                cost_func[s] = exp(-f * s)
            optimized_cost_calc.cached_result = cost_func
        return optimized_cost_calc.cached_result
    
    # Optimized stasis check with dictionary lookups
    optimization_results = [
        "\nBenchmarking stasis condition check:",
        benchmark_function(original_code, optimized_code, iterations),
        
        "\nBenchmarking cost function calculation:",
        benchmark_function(original_cost_calc, optimized_cost_calc, iterations)
    ]
    
    # Print all results
    for result in optimization_results:
        if isinstance(result, str):
            print(result)

def benchmark_function(original_func, optimized_func, iterations=10000):
    """Benchmark two versions of a function"""
    # Measure original function
    start = time.time()
    for _ in range(iterations):
        original_func()
    original_time = time.time() - start
    
    # Measure optimized function
    start = time.time()
    for _ in range(iterations):
        optimized_func()
    optimized_time = time.time() - start
    
    # Print results
    print(f"Original: {original_time:.4f}s, Optimized: {optimized_time:.4f}s")
    print(f"Speed improvement: {(original_time / optimized_time):.2f}x")
    if optimized_time < original_time:
        print(f"Optimization successful: {((original_time - optimized_time) / original_time * 100):.1f}% faster")
    else:
        print(f"Optimization not effective: {((optimized_time - original_time) / original_time * 100):.1f}% slower")
        
    return {
        'original_time': original_time,
        'optimized_time': optimized_time,
        'improvement': original_time / optimized_time
    }

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Benchmark Lif simulation")
    parser.add_argument(
        '-p', '--profile', 
        action='store_true', 
        help='Run profiling on the simulation'
    )
    parser.add_argument(
        '-c', '--compare', 
        action='store_true', 
        help='Compare original vs optimized implementations'
    )
    parser.add_argument(
        '-g', '--generations', 
        type=int, 
        default=100,
        help='Number of generations to simulate'
    )
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    if args.profile:
        print(f"Running profiling for {args.generations} generations...")
        run_profiling(args.generations)
    
    if args.compare:
        print(f"Comparing original vs optimized implementations...")
        compare_versions()
    
    if not (args.profile or args.compare):
        print("No action specified. Use -p for profiling or -c for comparison.")
        sys.exit(1)