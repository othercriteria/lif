"""Configuration parameters for Lif"""

from typing import Dict, Any, Optional
import argparse

# Model parameters
params: Dict[str, Any] = {
    'size': {'x': 80, 'y': 80},
    'toroidal': True,
    'standard': False,
    'alive_p': 0.1,
    'mut_p': 0.0001,
    'exchange_r': 0.001,
    'goh_r': 1.0,
    'goh_m': 'max',
    'fit_cost': 5.0,
    'outfile': 'lif_stats.csv'
}

def parse_args() -> argparse.Namespace:
    """Parse command line arguments and update params"""
    parser = argparse.ArgumentParser(description='Game of Life variant.')
    parser.add_argument('width', metavar='x', type=int, nargs='?',
                        default=params['size']['x'],
                        help='Grid width (default: %(default)s)')
    parser.add_argument('height', metavar='y', type=int, nargs='?',
                        default=params['size']['y'],
                        help='Grid height (default: %(default)s)')
    parser.add_argument('-alive_p', metavar='p', type=float,
                        default=params['alive_p'],
                        help='Alive stasis bit prob. (default: %(default)s)')
    parser.add_argument('-mut_p', metavar='p', type=float,
                        default=params['mut_p'],
                        help='Mutation bit prob. (default: %(default)s)')
    parser.add_argument('-exchange_r', metavar='r', type=float,
                        default=params['exchange_r'],
                        help='Exchange rate (default: %(default)s)')
    parser.add_argument('-goh_r', metavar='r', type=float,
                        default=params['goh_r'],
                        help='Gain of habitability rate (default: %(default)s)')
    parser.add_argument('-pick', metavar='mode', type=str,
                        default=params['goh_m'],
                        help='Habitability gain pick (default: %(default)s)')
    parser.add_argument('-fit_cost', metavar='c', type=float,
                        default=params['fit_cost'],
                        help='Fitness cost (default: %(default)s)')
    parser.add_argument('-nontoroidal', action='store_true',
                        help='Use nontoroidal topology')
    parser.add_argument('-output', metavar='FILE', type=str,
                        default=params['outfile'],
                        help='Output file for run stats (default: %(default)s)')
    parser.add_argument('-timing', action='store_true',
                        help='Run with Python profiling.')
    parser.add_argument('-blind', metavar='g', type=int, 
                        help='Profile without IO, terminate at set generation.')
    
    args = parser.parse_args()
    
    # If blind is set, timing is implied
    if args.blind:
        args.timing = True
        
    return args

def update_params(args: argparse.Namespace) -> None:
    """Update params based on command line arguments"""
    params['size']['x'] = args.width
    params['size']['y'] = args.height
    params['alive_p'] = args.alive_p
    params['mut_p'] = args.mut_p
    params['exchange_r'] = args.exchange_r
    params['goh_r'] = args.goh_r
    params['goh_m'] = args.pick
    params['fit_cost'] = args.fit_cost
    params['toroidal'] = not args.nontoroidal
    params['outfile'] = args.output