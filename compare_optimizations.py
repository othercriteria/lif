#!/usr/bin/env python
"""
Compare performance of original, Numba, and Cython implementations
"""

import sys
import os
import time
import random
from collections import defaultdict
import argparse

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def run_benchmarks():
    """Run benchmarks comparing original vs optimized implementations"""
    # Import original implementations
    from lif.utils.math import iid_set, weighted_choice
    
    # Import Numba implementations (if available)
    try:
        from lif.utils.numba_optimized import numba_iid_set, numba_weighted_choice, NUMBA_AVAILABLE
    except ImportError:
        NUMBA_AVAILABLE = False
        print("Numba not available, skipping Numba tests.")
        numba_iid_set = lambda p: set()
        numba_weighted_choice = lambda w: 0
    
    # Import Cython implementations (if available)
    try:
        from lif.utils.cython_optimized import cy_iid_set, cy_weighted_choice
        CYTHON_AVAILABLE = True
    except ImportError:
        CYTHON_AVAILABLE = False
        print("Cython module not built, skipping Cython tests.")
        cy_iid_set = lambda p: set()
        cy_weighted_choice = lambda w: 0

    # Function to benchmark and report results
    def benchmark_function(name, implementations, args, iterations=100000):
        print_header(f"Benchmarking {name} ({iterations:,} iterations)")
        
        results = {}
        for impl_name, func in implementations.items():
            if impl_name == "Numba" and not NUMBA_AVAILABLE:
                print(f"{impl_name:10}: Not available")
                continue
            if impl_name == "Cython" and not CYTHON_AVAILABLE:
                print(f"{impl_name:10}: Not available")
                continue
                
            # Warmup
            for _ in range(100):
                func(*args)
                
            # Timing
            start = time.time()
            for _ in range(iterations):
                func(*args)
            elapsed = time.time() - start
            
            results[impl_name] = elapsed
            print(f"{impl_name:10}: {elapsed:.6f}s")
        
        # Calculate and display speedups
        baseline = results.get("Original", 1.0)
        if baseline > 0:
            print("\nSpeedups compared to original:")
            for impl_name, elapsed in results.items():
                if impl_name != "Original":
                    speedup = baseline / elapsed
                    print(f"{impl_name:10}: {speedup:.2f}x")
        
        return results
    
    # Test random number generation
    random.seed(42)  # Set seed for reproducibility
    
    # Benchmark iid_set with various probability values
    for p in [0.1, 0.5, 0.9]:
        implementations = {
            "Original": iid_set,
            "Numba": numba_iid_set,
            "Cython": cy_iid_set,
        }
        benchmark_function(f"iid_set(p={p})", implementations, (p,))
    
    # Benchmark weighted_choice with different input sizes
    for size in [2, 5, 10]:
        weights = [random.random() for _ in range(size)]
        implementations = {
            "Original": weighted_choice,
            "Numba": numba_weighted_choice,
            "Cython": cy_weighted_choice,
        }
        benchmark_function(f"weighted_choice (size={size})", implementations, (weights,))

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Compare performance optimizations")
    parser.add_argument('--build-cython', action='store_true', 
                       help='Build Cython extensions before running benchmarks')
    parser.add_argument('--install-deps', action='store_true',
                       help='Install required dependencies (numba, cython, numpy)')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    if args.install_deps:
        print("Installing dependencies...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "numba", "cython", "numpy"])
    
    if args.build_cython:
        print("Building Cython extensions...")
        import subprocess
        subprocess.run([sys.executable, "setup_cython.py", "build_ext", "--inplace"])
    
    run_benchmarks()