"""Movement allocation strategies.

Each strategy receives a batch of agents to place each step and returns
{pillar_index: count} indicating WHERE to place them. The Model controls
HOW MANY are recruited per step (gradual recruitment over ~20 steps).
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import numpy as np


class AllocationStrategy(ABC):
    """Base class for movement allocation strategies."""

    @abstractmethod
    def reset(self, model):
        """Reset strategy state for a new run."""
        pass

    @abstractmethod
    def get_allocation(self, model, batch_size: int) -> Dict[int, int]:
        """Return {pillar_index: count} for placing batch_size agents this step."""
        pass


class SimultaneousStrategy(AllocationStrategy):
    """Distribute each batch of committed agents evenly across all pillars."""

    def reset(self, model):
        pass

    def get_allocation(self, model, batch_size: int) -> Dict[int, int]:
        n_pillars = len(model.pillars)
        base = batch_size // n_pillars
        remainder = batch_size % n_pillars
        allocation = {}
        for i in range(n_pillars):
            count = base + (1 if i < remainder else 0)
            if count > 0:
                allocation[i] = count
        return allocation


class SequentialStrategy(AllocationStrategy):
    """Allocate each batch entirely to one pillar at a time.
    Move to next pillar after current one tips (>50% defected)."""

    def __init__(self, pillar_order: Optional[list] = None):
        self._pillar_order = pillar_order
        self._current_idx = 0

    def reset(self, model):
        if self._pillar_order is None:
            self._pillar_order = list(range(len(model.pillars)))
        self._current_idx = 0

    def get_allocation(self, model, batch_size: int) -> Dict[int, int]:
        # Advance past tipped pillars
        while (self._current_idx < len(self._pillar_order) and
               model.pillars[self._pillar_order[self._current_idx]].tipped):
            self._current_idx += 1

        if self._current_idx >= len(self._pillar_order):
            # All pillars tipped or exhausted — place in least-defected
            rates = [(i, model.pillars[i].defection_rate) for i in range(len(model.pillars))]
            rates.sort(key=lambda x: x[1])
            return {rates[0][0]: batch_size}

        target = self._pillar_order[self._current_idx]
        return {target: batch_size}


class LeastLoyalFirstStrategy(AllocationStrategy):
    """Sequential strategy, but order pillars by lowest mean threshold first."""

    def __init__(self):
        self._inner: Optional[SequentialStrategy] = None

    def reset(self, model):
        pillar_thresholds = []
        for i, pillar in enumerate(model.pillars):
            mean_t = np.mean([a.threshold for a in pillar.agents.values()])
            pillar_thresholds.append((i, mean_t))
        pillar_thresholds.sort(key=lambda x: x[1])
        order = [idx for idx, _ in pillar_thresholds]

        self._inner = SequentialStrategy(pillar_order=order)
        self._inner.reset(model)

    def get_allocation(self, model, batch_size: int) -> Dict[int, int]:
        return self._inner.get_allocation(model, batch_size)


class RandomStrategy(AllocationStrategy):
    """Allocate each batch randomly across pillars."""

    def __init__(self, rng: Optional[np.random.Generator] = None):
        self._rng = rng or np.random.default_rng()

    def reset(self, model):
        pass

    def get_allocation(self, model, batch_size: int) -> Dict[int, int]:
        n_pillars = len(model.pillars)
        probs = self._rng.dirichlet(np.ones(n_pillars))
        counts = self._rng.multinomial(batch_size, probs)
        return {i: int(c) for i, c in enumerate(counts) if c > 0}
