"""Core model: Agent, Pillar, and Model classes."""

from enum import IntEnum
from typing import List, Dict, Optional, Tuple
import numpy as np
import networkx as nx
from .config import ModelConfig, PillarConfig, CouplingConfig


class State(IntEnum):
    LOYAL = 0
    WAVERING = 1
    DEFECTED = 2


class Agent:
    __slots__ = ("id", "pillar_id", "state", "threshold", "is_opinion_leader",
                 "bridge_partner", "influence_multiplier")

    def __init__(self, agent_id: int, pillar_id: int, threshold: float,
                 is_opinion_leader: bool = False, influence_multiplier: float = 1.0):
        self.id = agent_id
        self.pillar_id = pillar_id
        self.state = State.LOYAL
        self.threshold = threshold
        self.is_opinion_leader = is_opinion_leader
        self.influence_multiplier = influence_multiplier
        self.bridge_partner: Optional["Agent"] = None


class Pillar:
    def __init__(self, index: int, config: PillarConfig, rng: np.random.Generator):
        self.index = index
        self.config = config
        self.rng = rng
        self.graph: nx.Graph = self._build_network()
        self.agents: Dict[int, Agent] = {}
        self.tipped = False
        self._coupling_applied: set = set()  # Track which couplings have fired

        self._populate_agents()

    def _build_network(self) -> nx.Graph:
        n = self.config.size
        k = self.config.avg_degree
        topo = self.config.topology

        if topo == "barabasi_albert":
            m = max(1, k // 2)
            return nx.barabasi_albert_graph(n, m, seed=int(self.rng.integers(2**31)))
        elif topo == "watts_strogatz":
            return nx.watts_strogatz_graph(n, k, 0.3, seed=int(self.rng.integers(2**31)))
        elif topo == "erdos_renyi":
            p = k / (n - 1) if n > 1 else 0
            return nx.erdos_renyi_graph(n, p, seed=int(self.rng.integers(2**31)))
        else:
            raise ValueError(f"Unknown topology: {topo}")

    def _populate_agents(self):
        n = self.config.size
        mu = self.config.threshold_mean
        sigma = self.config.threshold_std

        # Right-skewed threshold distribution using beta distribution
        # Convert mean/std to alpha/beta parameters
        # For right-skew: most agents have moderate-high thresholds, few have low
        alpha, beta_param = self._mean_std_to_beta_params(mu, sigma)
        thresholds = self.rng.beta(alpha, beta_param, size=n)
        thresholds = np.clip(thresholds, 0.01, 0.99)

        # Designate opinion leaders: top-degree nodes
        degrees = dict(self.graph.degree())
        sorted_nodes = sorted(degrees, key=degrees.get, reverse=True)
        n_leaders = max(1, int(n * self.config.opinion_leader_fraction))
        leader_set = set(sorted_nodes[:n_leaders])

        multiplier = self.config.opinion_leader_multiplier
        for node_id in self.graph.nodes():
            is_leader = node_id in leader_set
            agent = Agent(
                agent_id=node_id,
                pillar_id=self.index,
                threshold=float(thresholds[node_id]),
                is_opinion_leader=is_leader,
                influence_multiplier=multiplier if is_leader else 1.0,
            )
            self.agents[node_id] = agent

    @staticmethod
    def _mean_std_to_beta_params(mu: float, sigma: float):
        """Convert desired mean and std to beta distribution parameters."""
        mu = np.clip(mu, 0.01, 0.99)
        variance = sigma ** 2
        max_var = mu * (1 - mu)
        if variance >= max_var:
            variance = max_var * 0.9
        common = (mu * (1 - mu) / variance) - 1
        alpha = mu * common
        beta_param = (1 - mu) * common
        return max(alpha, 0.5), max(beta_param, 0.5)

    @property
    def size(self) -> int:
        return len(self.agents)

    @property
    def defection_rate(self) -> float:
        if not self.agents:
            return 0.0
        defected = sum(1 for a in self.agents.values() if a.state == State.DEFECTED)
        return defected / len(self.agents)

    @property
    def n_defected(self) -> int:
        return sum(1 for a in self.agents.values() if a.state == State.DEFECTED)

    def add_committed_agents(self, count: int):
        """Insert committed minority agents into the network."""
        existing_nodes = list(self.graph.nodes())
        if not existing_nodes:
            return

        for _ in range(count):
            new_id = max(self.graph.nodes()) + 1 if self.graph.nodes() else 0
            self.graph.add_node(new_id)
            # Connect to random existing nodes (avg_degree connections)
            n_connections = min(self.config.avg_degree, len(existing_nodes))
            targets = self.rng.choice(existing_nodes, size=n_connections, replace=False)
            for t in targets:
                self.graph.add_edge(new_id, t)

            agent = Agent(
                agent_id=new_id,
                pillar_id=self.index,
                threshold=0.0,
                is_opinion_leader=False,
                influence_multiplier=1.0,
            )
            agent.state = State.DEFECTED
            self.agents[new_id] = agent

    def step_influence(self) -> int:
        """Run one round of intra-pillar threshold influence. Returns count of new defections."""
        new_defections = 0
        agents_to_update = []

        for node_id, agent in self.agents.items():
            if agent.state == State.DEFECTED:
                continue

            neighbors = list(self.graph.neighbors(node_id))
            if not neighbors:
                continue

            # Calculate weighted defection fraction
            total_weight = 0.0
            defected_weight = 0.0
            for nb_id in neighbors:
                nb_agent = self.agents.get(nb_id)
                if nb_agent is None:
                    continue
                weight = nb_agent.influence_multiplier
                total_weight += weight
                if nb_agent.state == State.DEFECTED:
                    defected_weight += weight

            if total_weight == 0:
                continue

            defection_fraction = defected_weight / total_weight

            if defection_fraction > 0 and agent.state == State.LOYAL:
                agent.state = State.WAVERING

            if defection_fraction >= agent.threshold:
                agents_to_update.append(agent)

        for agent in agents_to_update:
            agent.state = State.DEFECTED
            new_defections += 1

        return new_defections


class StepRecord:
    __slots__ = ("step", "pillar_defection_rates", "total_defection_rate",
                 "pillar_n_defected", "total_n_defected")

    def __init__(self, step: int, pillar_rates: List[float], total_rate: float,
                 pillar_n_defected: List[int], total_n_defected: int):
        self.step = step
        self.pillar_defection_rates = pillar_rates
        self.total_defection_rate = total_rate
        self.pillar_n_defected = pillar_n_defected
        self.total_n_defected = total_n_defected


class Model:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        self.pillars: List[Pillar] = []
        self.bridge_pairs: List[Tuple[Agent, Agent]] = []
        self.history: List[StepRecord] = []
        self.step_count = 0

        self._build_pillars()
        self._setup_bridge_agents()

    def _build_pillars(self):
        for i, pc in enumerate(self.config.pillars):
            pillar = Pillar(i, pc, self.rng)
            self.pillars.append(pillar)

    def _setup_bridge_agents(self):
        """Create bridge agents for bridge-type couplings."""
        for coupling in self.config.couplings:
            if coupling.coupling_type != "bridge":
                continue

            src = self.pillars[coupling.source]
            tgt = self.pillars[coupling.target]
            n_bridges = max(1, int(min(src.size, tgt.size) * coupling.strength))

            src_candidates = [a for a in src.agents.values()
                              if a.bridge_partner is None and a.state != State.DEFECTED]
            tgt_candidates = [a for a in tgt.agents.values()
                              if a.bridge_partner is None and a.state != State.DEFECTED]

            n_bridges = min(n_bridges, len(src_candidates), len(tgt_candidates))
            if n_bridges == 0:
                continue

            src_chosen = self.rng.choice(src_candidates, size=n_bridges, replace=False)
            tgt_chosen = self.rng.choice(tgt_candidates, size=n_bridges, replace=False)

            for sa, ta in zip(src_chosen, tgt_chosen):
                sa.bridge_partner = ta
                ta.bridge_partner = sa
                self.bridge_pairs.append((sa, ta))

    @property
    def total_population(self) -> int:
        return sum(p.size for p in self.pillars)

    @property
    def total_defection_rate(self) -> float:
        total = sum(p.size for p in self.pillars)
        defected = sum(p.n_defected for p in self.pillars)
        return defected / total if total > 0 else 0.0

    def apply_couplings(self):
        """Check and apply inter-pillar coupling effects."""
        for coupling in self.config.couplings:
            if coupling.coupling_type == "bridge":
                continue  # Bridge handled in step via bridge_pairs

            src = self.pillars[coupling.source]
            tgt = self.pillars[coupling.target]
            coupling_key = (coupling.source, coupling.target, coupling.coupling_type)

            if coupling_key in tgt._coupling_applied:
                continue

            if src.defection_rate >= self.config.coupling_trigger:
                if coupling.coupling_type == "cascade":
                    for agent in tgt.agents.values():
                        if agent.state != State.DEFECTED:
                            agent.threshold *= (1 - coupling.strength)
                elif coupling.coupling_type == "mechanical":
                    non_defected = [a for a in tgt.agents.values() if a.state != State.DEFECTED]
                    n_replace = int(len(tgt.agents) * coupling.strength)
                    if non_defected and n_replace > 0:
                        n_replace = min(n_replace, len(non_defected))
                        chosen = self.rng.choice(non_defected, size=n_replace, replace=False)
                        for agent in chosen:
                            agent.state = State.DEFECTED

                tgt._coupling_applied.add(coupling_key)

    def apply_bridge_defections(self):
        """Propagate defections through bridge agents."""
        for a1, a2 in self.bridge_pairs:
            if a1.state == State.DEFECTED and a2.state != State.DEFECTED:
                a2.state = State.DEFECTED
            elif a2.state == State.DEFECTED and a1.state != State.DEFECTED:
                a1.state = State.DEFECTED

    def record_state(self):
        """Log current state."""
        pillar_rates = [p.defection_rate for p in self.pillars]
        pillar_n = [p.n_defected for p in self.pillars]
        total_n = sum(pillar_n)
        total_rate = total_n / self.total_population if self.total_population > 0 else 0.0
        record = StepRecord(self.step_count, pillar_rates, total_rate, pillar_n, total_n)
        self.history.append(record)

    def step(self, committed_allocation: Optional[Dict[int, int]] = None) -> int:
        """Execute one time step. Returns total new defections across all pillars."""
        # 1. Movement allocation
        if committed_allocation:
            for pillar_idx, count in committed_allocation.items():
                if count > 0:
                    self.pillars[pillar_idx].add_committed_agents(count)

        # 2. Intra-pillar influence
        total_new = 0
        for pillar in self.pillars:
            total_new += pillar.step_influence()

        # 3. Bridge propagation
        self.apply_bridge_defections()

        # 4. Inter-pillar coupling
        self.apply_couplings()

        # 5. Update tipped status
        for pillar in self.pillars:
            if pillar.defection_rate >= 0.50:
                pillar.tipped = True

        # 6. Record
        self.step_count += 1
        self.record_state()

        return total_new

    def run_with_strategy(self, strategy, total_committed: int,
                          recruitment_steps: int = 20) -> List[StepRecord]:
        """Run model with gradual agent recruitment over recruitment_steps.

        Each step, the movement recruits agents_per_step new committed agents,
        placing them according to the strategy. After all agents are placed,
        dynamics continue until equilibrium.

        This models real-world recruitment: the movement builds committed
        membership over time, concentrating (sequential) or spreading
        (simultaneous) its recruitment effort.
        """
        strategy.reset(self)
        self.record_state()

        agents_per_step = max(1, total_committed // recruitment_steps)
        committed_placed = 0
        no_change_count = 0

        for _ in range(self.config.max_steps):
            # Recruit new committed agents this step
            new_allocation = None
            remaining = total_committed - committed_placed
            if remaining > 0:
                batch = min(agents_per_step, remaining)
                # Strategy says WHERE to place this batch
                allocation = strategy.get_allocation(self, batch)
                if allocation:
                    new_allocation = allocation
                    committed_placed += sum(allocation.values())

            new_defections = self.step(new_allocation)

            if new_defections == 0 and committed_placed >= total_committed:
                no_change_count += 1
            else:
                no_change_count = 0

            if no_change_count >= self.config.equilibrium_window:
                break

        return self.history
