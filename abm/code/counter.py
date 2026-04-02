"""Counter-mobilization strategies and movement defenses (Experiment 4)."""

from typing import Optional
import numpy as np
import networkx as nx
from .model import Model, State, Pillar


class CounterStrategy:
    """Base class for regime counter-mobilization strategies."""

    def apply(self, model: Model, target_pillar_idx: int, rng: np.random.Generator):
        raise NotImplementedError


class Fragmentation(CounterStrategy):
    """Split a pillar's network into two disconnected sub-networks."""

    def apply(self, model: Model, target_pillar_idx: int, rng: np.random.Generator):
        pillar = model.pillars[target_pillar_idx]
        g = pillar.graph
        nodes = list(g.nodes())
        if len(nodes) < 4:
            return

        # Find edges that bridge the two halves and remove them
        rng.shuffle(nodes)
        half = len(nodes) // 2
        group_a = set(nodes[:half])
        group_b = set(nodes[half:])

        edges_to_remove = [(u, v) for u, v in g.edges()
                           if (u in group_a and v in group_b) or
                              (u in group_b and v in group_a)]
        g.remove_edges_from(edges_to_remove)


class Atomization(CounterStrategy):
    """Randomly remove edges from a pillar's network to reduce density."""

    def __init__(self, removal_fraction: float = 0.3):
        self.removal_fraction = removal_fraction

    def apply(self, model: Model, target_pillar_idx: int, rng: np.random.Generator):
        pillar = model.pillars[target_pillar_idx]
        g = pillar.graph
        edges = list(g.edges())
        if not edges:
            return
        n_remove = max(1, int(len(edges) * self.removal_fraction))
        indices = rng.choice(len(edges), size=min(n_remove, len(edges)), replace=False)
        edges_to_remove = [edges[i] for i in indices]
        g.remove_edges_from(edges_to_remove)


class Cooptation(CounterStrategy):
    """Increase thresholds of randomly selected agents (add material cost to defection)."""

    def __init__(self, fraction: float = 0.2, threshold_increase: float = 0.3):
        self.fraction = fraction
        self.threshold_increase = threshold_increase

    def apply(self, model: Model, target_pillar_idx: int, rng: np.random.Generator):
        pillar = model.pillars[target_pillar_idx]
        non_defected = [a for a in pillar.agents.values() if a.state != State.DEFECTED]
        if not non_defected:
            return
        n_target = max(1, int(len(non_defected) * self.fraction))
        chosen = rng.choice(non_defected, size=min(n_target, len(non_defected)), replace=False)
        for agent in chosen:
            agent.threshold = min(0.99, agent.threshold + self.threshold_increase)


class Decapitation(CounterStrategy):
    """Remove opinion leader agents from the network."""

    def apply(self, model: Model, target_pillar_idx: int, rng: np.random.Generator):
        pillar = model.pillars[target_pillar_idx]
        leaders = [a for a in pillar.agents.values()
                   if a.is_opinion_leader and a.state != State.DEFECTED]
        for leader in leaders:
            if leader.id in pillar.graph:
                pillar.graph.remove_node(leader.id)
            del pillar.agents[leader.id]


# Movement defenses

class MovementDefense:
    """Base class for movement defenses against counter-mobilization."""

    def apply(self, model: Model, rng: np.random.Generator):
        raise NotImplementedError


class DistributedLeadership(MovementDefense):
    """Mitigates decapitation: redistribute opinion leader status to remaining high-degree nodes."""

    def apply(self, model: Model, rng: np.random.Generator):
        for pillar in model.pillars:
            has_leader = any(a.is_opinion_leader for a in pillar.agents.values()
                           if a.state == State.DEFECTED)
            if not has_leader:
                continue

            non_defected = [a for a in pillar.agents.values()
                           if a.state != State.DEFECTED and not a.is_opinion_leader]
            if not non_defected:
                continue

            degrees = {a.id: pillar.graph.degree(a.id) for a in non_defected
                       if a.id in pillar.graph}
            if not degrees:
                continue

            sorted_by_degree = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
            n_new_leaders = max(1, int(len(non_defected) * pillar.config.opinion_leader_fraction))
            for node_id, _ in sorted_by_degree[:n_new_leaders]:
                agent = pillar.agents[node_id]
                agent.is_opinion_leader = True
                agent.influence_multiplier = pillar.config.opinion_leader_multiplier


class RedundantChannels(MovementDefense):
    """Mitigates atomization/fragmentation: add new edges to restore connectivity."""

    def __init__(self, edges_to_add_fraction: float = 0.2):
        self.fraction = edges_to_add_fraction

    def apply(self, model: Model, rng: np.random.Generator):
        for pillar in model.pillars:
            g = pillar.graph
            nodes = list(g.nodes())
            if len(nodes) < 3:
                continue
            n_edges = max(1, int(len(nodes) * self.fraction))
            for _ in range(n_edges):
                u, v = rng.choice(nodes, size=2, replace=False)
                if not g.has_edge(u, v):
                    g.add_edge(u, v)


class AlternativeInterdependence(MovementDefense):
    """Mitigates co-optation: reduce thresholds of agents who have been co-opted,
    modeling the creation of alternative support structures."""

    def __init__(self, threshold_reduction: float = 0.15):
        self.reduction = threshold_reduction

    def apply(self, model: Model, rng: np.random.Generator):
        for pillar in model.pillars:
            for agent in pillar.agents.values():
                if agent.state != State.DEFECTED and agent.threshold > 0.5:
                    agent.threshold = max(0.01, agent.threshold - self.reduction)
