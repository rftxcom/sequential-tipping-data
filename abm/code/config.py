"""Default parameters and experiment configurations for the Sequential Tipping Model."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


@dataclass
class PillarConfig:
    name: str
    size: int
    topology: str  # "barabasi_albert", "watts_strogatz", "erdos_renyi"
    avg_degree: int
    threshold_mean: float
    threshold_std: float
    opinion_leader_fraction: float = 0.05
    opinion_leader_multiplier: float = 3.0


@dataclass
class CouplingConfig:
    source: int
    target: int
    coupling_type: str  # "cascade", "mechanical", "bridge"
    strength: float  # delta for cascade, fraction for mechanical, fraction for bridge


@dataclass
class ModelConfig:
    pillars: List[PillarConfig] = field(default_factory=list)
    couplings: List[CouplingConfig] = field(default_factory=list)
    coupling_trigger: float = 0.50
    max_steps: int = 500
    equilibrium_window: int = 10
    seed: Optional[int] = None

    @staticmethod
    def default() -> "ModelConfig":
        pillars = [
            PillarConfig("Military",     200, "barabasi_albert", 8,  0.35, 0.15),
            PillarConfig("Legislature",  300, "watts_strogatz",  6,  0.30, 0.12),
            PillarConfig("Judiciary",     150, "erdos_renyi",     10, 0.40, 0.15),
            PillarConfig("Business",      500, "erdos_renyi",     3,  0.50, 0.20),
            PillarConfig("Religious",     100, "watts_strogatz",  12, 0.25, 0.10),
        ]
        couplings = [
            CouplingConfig(0, 1, "cascade",    0.25),  # Military -> Legislature
            CouplingConfig(0, 2, "cascade",    0.20),  # Military -> Judiciary
            CouplingConfig(1, 3, "cascade",    0.15),  # Legislature -> Business
            CouplingConfig(1, 4, "cascade",    0.10),  # Legislature -> Religious
            CouplingConfig(4, 0, "bridge",     0.05),  # Religious-Military bridge
            CouplingConfig(2, 1, "cascade",    0.10),  # Judiciary -> Legislature
        ]
        return ModelConfig(pillars=pillars, couplings=couplings)


@dataclass
class ExperimentConfig:
    n_replications: int = 100
    c_values: Optional[List[float]] = None  # Fraction of total population
    c_min: float = 0.01
    c_max: float = 0.30
    c_steps: int = 30
    n_workers: Optional[int] = None  # None = use all CPUs

    def get_c_range(self) -> List[float]:
        if self.c_values is not None:
            return self.c_values
        step = (self.c_max - self.c_min) / self.c_steps
        return [self.c_min + i * step for i in range(self.c_steps + 1)]
