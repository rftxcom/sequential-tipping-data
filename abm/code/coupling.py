"""Inter-pillar coupling mechanisms.

Coupling logic is implemented directly in Model.apply_couplings() and
Model.apply_bridge_defections() in model.py. This module provides helper
functions for constructing and modifying coupling configurations, and for
analyzing coupling effects in experiments.
"""

from typing import List, Dict, Tuple, Optional
from .config import CouplingConfig, ModelConfig


def no_coupling_config() -> List[CouplingConfig]:
    """Return an empty coupling list (pillars are independent)."""
    return []


def cascade_only_config() -> List[CouplingConfig]:
    """Return the default coupling matrix with only cascade couplings."""
    return [
        CouplingConfig(0, 1, "cascade", 0.25),
        CouplingConfig(0, 2, "cascade", 0.20),
        CouplingConfig(1, 3, "cascade", 0.15),
        CouplingConfig(1, 4, "cascade", 0.10),
        CouplingConfig(2, 1, "cascade", 0.10),
    ]


def mixed_coupling_config() -> List[CouplingConfig]:
    """Return the full default coupling matrix (cascade + bridge)."""
    return [
        CouplingConfig(0, 1, "cascade",    0.25),
        CouplingConfig(0, 2, "cascade",    0.20),
        CouplingConfig(1, 3, "cascade",    0.15),
        CouplingConfig(1, 4, "cascade",    0.10),
        CouplingConfig(4, 0, "bridge",     0.05),
        CouplingConfig(2, 1, "cascade",    0.10),
    ]


def full_mixed_config() -> List[CouplingConfig]:
    """Return a coupling config with all three types for testing."""
    return [
        CouplingConfig(0, 1, "cascade",    0.25),
        CouplingConfig(0, 2, "mechanical", 0.30),
        CouplingConfig(1, 3, "cascade",    0.15),
        CouplingConfig(1, 4, "cascade",    0.10),
        CouplingConfig(4, 0, "bridge",     0.05),
        CouplingConfig(2, 1, "cascade",    0.10),
        CouplingConfig(3, 2, "mechanical", 0.15),
    ]


def measure_effective_threshold(model, pillar_idx: int) -> float:
    """Calculate the current mean effective threshold of non-defected agents in a pillar."""
    from .model import State
    pillar = model.pillars[pillar_idx]
    thresholds = [a.threshold for a in pillar.agents.values() if a.state != State.DEFECTED]
    if not thresholds:
        return 0.0
    return sum(thresholds) / len(thresholds)


def coupling_effect_size(threshold_before: float, threshold_after: float) -> float:
    """Calculate the proportional reduction in effective threshold."""
    if threshold_before == 0:
        return 0.0
    return (threshold_before - threshold_after) / threshold_before
