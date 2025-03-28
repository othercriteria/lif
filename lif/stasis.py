"""Stasis operations for Lif"""

from itertools import product
from typing import Dict, List, Set, Tuple

# Type definitions
StasisKey = Tuple[bool, ...]
StasisValue = int
StasisSet = Set[int]

# Precompute stasis operations
s_str: Dict[StasisKey, str] = {}
s_count: Dict[StasisKey, int] = {}
s_list: Dict[StasisKey, List[int]] = {}
s_set: Dict[StasisKey, Set[int]] = {}
s_min: Dict[StasisKey, int] = {}
s_max: Dict[StasisKey, int] = {}
s_gain: Dict[StasisKey, Dict[int, StasisKey]] = {}
s_lose: Dict[StasisKey, Dict[int, StasisKey]] = {}
s_lose_min: Dict[StasisKey, StasisKey] = {}
s_lose_max: Dict[StasisKey, StasisKey] = {}

for k in product([False, True], repeat=9):
    count = sum(k)
    as_list = [i for i in range(9) if k[i]]
    as_set = {i for i in range(9) if k[i]}

    s_count[k] = sum(k)
    s_str[k] = str(as_set)
    s_list[k] = as_list
    s_set[k] = as_set

    s_gain[k] = {}
    for v in range(9):
        k_l = list(k)
        k_l[v] = True
        s_gain[k][v] = tuple(k_l)

    s_lose[k] = {}
    for v in range(9):
        k_l = list(k)
        k_l[v] = False
        s_lose[k][v] = tuple(k_l)

    if count > 0:
        s_min[k] = min(as_list)
        s_max[k] = max(as_list)
        s_lose_min[k] = s_lose[k][s_min[k]]
        s_lose_max[k] = s_lose[k][s_max[k]]

stasis_none: StasisKey = tuple([False] * 9)
stasis_all: StasisKey = tuple([True] * 9)

def set_to_stasis(s: StasisSet) -> StasisKey:
    """Convert a set of indices to a stasis tuple"""
    length = len(s)
    if length == 9:
        return stasis_all
    elif length == 0:
        return stasis_none
    else:
        arr = [False] * 9
        for i in s:
            arr[i] = True
        return tuple(arr)