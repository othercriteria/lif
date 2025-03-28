"""Cell models for Lif"""

from typing import Dict, Set, Tuple, Optional, Any
from itertools import product
import random

from .stasis import stasis_all, set_to_stasis, s_set, StasisKey, StasisSet
from .utils.math import iid_set
from .config import params

# Global parent counter
parent_counter: int = 0

class Empty:
    """Empty cell representation"""
    alive: bool = False
    
    def __init__(self, stasis: Optional[StasisKey] = None):
        if not stasis:
            self.stasis: StasisKey = stasis_all
        else:
            self.stasis = stasis

# Create singleton instances of Empty cells
empty_init = Empty()
empty: Dict[StasisKey, Empty] = {}
for k in product([False, True], repeat=9):
    empty[k] = Empty(k)

class Alive:
    """Alive cell representation"""
    alive: bool = True
    parent: int = 0
    stasis: StasisKey = stasis_all
    
    def __init__(self, blank: bool = False):
        if not blank:
            global parent_counter
            parent_counter += 1
            self.parent = parent_counter
            self.stasis = set_to_stasis(iid_set(params['alive_p']))

    def child(self, new_stasis: StasisKey) -> 'Alive':
        """Create a child cell with the same parent but different stasis"""
        new = Alive(blank=True)
        new.parent = self.parent
        new.stasis = new_stasis
        return new

def mutate(parent: Alive) -> Alive:
    """Create a mutated version of the parent cell"""
    mut = iid_set(params['mut_p'])
    if sum(mut) > 0:
        new_stasis_mut = s_set[parent.stasis].symmetric_difference(mut)
        return parent.child(set_to_stasis(new_stasis_mut))
    else:
        return parent