# Sequential Tipping Agent-Based Model: Specification Document

## For Implementation in Claude Code (Python)

### Purpose

Build an agent-based model of sequential tipping across coupled institutional networks (pillars). The model tests the core claim of Sequential Tipping Theory: that a movement sequencing tipping points across institutional pillars, starting with the most susceptible, outperforms both simultaneous pressure across all pillars and undifferentiated mass mobilization. The model also produces threshold band estimates that can be compared to the three-threshold model (activation at 3.5-5%, cascade at 10-16%, convention change at ~25%).

This model extends Chenoweth, Hocking, and Marks (2022), which tested pillar-focused strategy on a single-lattice agent-based model with four agent types. Our model adds: (a) multiple structurally distinct pillar networks with different internal topologies, (b) three distinct inter-pillar transmission mechanisms, and (c) threshold dynamics within each pillar that produce measurable phase transitions.

---

### Architecture

**Language:** Python 3.10+
**Dependencies:** NetworkX (network construction and analysis), NumPy (random number generation, statistics), Matplotlib (visualization), pandas (data collection and output). Optionally Mesa if the framework simplifies agent scheduling, but a custom implementation is acceptable if cleaner.

**Output directory:** Save all output files (CSV data, PNG charts, summary statistics) to `~/projects/sequential-tipping-model/output/`

---

### Model Components

#### 1. Agents

Each agent represents an individual member of an institutional pillar. Agents have the following properties:

```
Agent:
  pillar_id: int          # Which pillar this agent belongs to (0 to N_pillars-1)
  threshold: float        # Individual activation threshold (0.0 to 1.0)
                          # The fraction of network neighbors who must be active
                          # before this agent activates
  active: bool            # Whether this agent has activated (defected from status quo)
  committed: bool         # Whether this agent is a committed minority member
                          # (immune to deactivation; threshold effectively 0)
  opinion_leader: bool    # Whether this agent is an opinion leader
                          # (has higher degree and influence weight)
  influence_weight: float # How much this agent's activation counts toward
                          # neighbors' threshold calculations (default 1.0;
                          # opinion leaders get higher weight, e.g., 2.0-3.0)
```

#### 2. Pillar Networks

Each pillar is a separate network (graph) with its own topology. The model supports N pillars (default: 5, representing a simplified institutional landscape).

**Pillar types and their network properties:**

| Pillar Type | Network Topology | N Agents | Avg Degree | Opinion Leader % | Tipping Domain Strength |
|------------|-----------------|----------|------------|-----------------|----------------------|
| Strong (e.g., military, legislature) | Small-world (Watts-Strogatz) | 200-500 | 10-20 | 5% | High: dense connections, high clustering |
| Moderate (e.g., professional association, party primary electorate) | Erdos-Renyi random | 500-1000 | 5-10 | 3% | Medium: moderate connections |
| Weak (e.g., business community, media) | Barabasi-Albert scale-free | 1000-2000 | 3-5 | 1% | Low: sparse, hub-dominated |

**Threshold distribution within each pillar:**
Draw individual thresholds from a Beta distribution with parameters calibrated to produce Rogers' adopter category structure:
- ~2.5% of agents have thresholds below 0.05 (innovators: will activate with minimal social proof)
- ~13.5% have thresholds between 0.05 and 0.20 (early adopters: activate when respected peers do)
- ~34% have thresholds between 0.20 and 0.50 (early majority: require substantial social proof)
- ~34% have thresholds between 0.50 and 0.80 (late majority: activate under strong pressure)
- ~16% have thresholds above 0.80 (laggards: resist until nearly universal adoption)

Use Beta(2, 5) as a starting distribution and adjust alpha/beta parameters to match these approximate bands. The exact distribution matters less than the shape: right-skewed with a small low-threshold tail.

**Opinion leaders:**
Randomly designate a fraction of agents as opinion leaders. Opinion leaders should be among the higher-degree nodes in the network (top 20% by degree). Give them influence_weight = 2.5 (their activation counts 2.5x toward neighbors' threshold calculations). This models Rogers' finding that opinion leader adoption disproportionately drives cascade.

#### 3. Inter-Pillar Connections

Pillars are connected to each other through three types of transmission mechanisms. Each connection type has a distinct effect on threshold dynamics in the receiving pillar.

**Type A: Institutional Signaling**
When a pillar tips (fraction of active agents exceeds a signaling threshold, default 0.15), it sends a signal to connected pillars. The signal lowers all agents' thresholds in the receiving pillar by a fixed amount (default: 0.05, meaning a 5-percentage-point reduction). This models: "when the military stands down, the police recalculate."

Implementation: maintain a directed graph of pillar-to-pillar signaling connections. At each timestep, check if any pillar has crossed its signaling threshold. If so, apply the threshold reduction to all agents in connected pillars. Signal is one-time (does not compound from the same source).

**Type B: Material Interdependence (Constraint Removal)**
When a specific pillar tips, it removes a constraint that was raising thresholds in another pillar. Model this as: pillar X tipping reduces thresholds in pillar Y by a larger amount (default: 0.10) but only for a specific subset of agents (those whose thresholds were artificially elevated by the constraint, e.g., the top 30% by threshold). This models: "when the military defects, the coercive backstop that kept the bureaucracy compliant disappears."

Implementation: define constraint relationships as (source_pillar, target_pillar, affected_fraction, threshold_reduction). When source tips, apply reduction to the highest-threshold fraction of agents in target.

**Type C: Mechanical Transmission (Appointment Chain)**
When a pillar tips, it directly replaces a fraction of agents in the connected pillar with committed agents. This models the SBC appointment chain: tipping the presidency physically replaces committee members. This is deterministic, not probabilistic.

Implementation: when source pillar's active fraction exceeds the mechanical threshold (default: 0.50, representing institutional control), replace a fraction (default: 0.10 per timestep) of non-committed agents in the target pillar with new committed agents (threshold = 0, committed = True). Continue replacement each timestep until the replacement budget is exhausted (default: 30% of target pillar's total agents).

#### 4. Movement Strategies (Experimental Conditions)

The model tests four strategies:

**Strategy 1: Mass Mobilization**
Committed agents are distributed uniformly across all pillars in proportion to each pillar's size. Total committed fraction: a parameter (sweep from 1% to 15%). No targeting. No sequencing.

**Strategy 2: Simultaneous Pillar Pressure**
Same total committed fraction, but concentrated equally across the top 3 strongest tipping domains (rather than spread across all pillars). No sequencing: all three pillars are pressured simultaneously.

**Strategy 3: Sequential Tipping (Weakest-First)**
Same total committed fraction, concentrated entirely in the single pillar with the lowest average threshold (the "weakest" or least loyal). Once that pillar tips (active fraction > cascade threshold), redistribute a fraction of the remaining committed agent budget to the next weakest pillar. Continue sequencing.

**Strategy 4: Sequential Tipping (Strongest-Domain-First)**
Same total committed fraction, concentrated in the strongest tipping domain (highest network density, most opinion leaders). Theory predicts this should tip faster than weakest-first for the initial pillar, but the comparison tests whether domain strength or loyalty proximity matters more for sequencing.

#### 5. Activation Dynamics (Per Timestep)

Each timestep:

1. For each agent, calculate the weighted fraction of active neighbors:
   ```
   active_influence = sum(influence_weight for neighbor in neighbors if neighbor.active)
   total_influence = sum(influence_weight for neighbor in neighbors)
   neighbor_fraction = active_influence / total_influence
   ```

2. If `neighbor_fraction >= agent.threshold` and agent is not already active, activate the agent.

3. **Stochastic element (per Macy & Evtushenko, 2020):** With small probability epsilon (default: 0.02), an inactive agent activates even if below threshold (spontaneous instigation). With the same probability, an active non-committed agent deactivates (representing wavering). Committed agents never deactivate. This introduces the realistic behavioral noise that Macy & Evtushenko showed stabilizes cascade predictions.

4. Check inter-pillar transmission conditions (signaling thresholds, mechanical replacement triggers).

5. Record state: fraction active in each pillar, total system active fraction, timestep number.

6. Termination: run for max 500 timesteps or until system reaches equilibrium (no state changes for 10 consecutive timesteps).

---

### Experimental Design

#### Experiment 1: Strategy Comparison

**Question:** Does sequential tipping outperform mass mobilization and simultaneous pressure?

**Parameters:**
- N_pillars: 5 (2 strong, 2 moderate, 1 weak)
- Total committed fraction: sweep from 1% to 15% in 1% increments
- Inter-pillar connections: define a realistic connection matrix (strong pillars signal to moderate; moderate signal to weak; one mechanical connection between the two strong pillars)
- Strategies: all four
- Replications: 100 per condition (to account for stochastic variation)

**Output:**
- For each strategy and committed fraction: mean and standard deviation of (a) fraction of pillars tipped (active > 50%), (b) total system active fraction at equilibrium, (c) timesteps to first pillar tip, (d) timesteps to system-level cascade (3+ pillars tipped)
- Plot: committed fraction (x-axis) vs. fraction of pillars tipped (y-axis), one line per strategy
- CSV: full run data for statistical analysis

#### Experiment 2: Threshold Band Detection

**Question:** Do the three threshold bands (activation ~3.5-5%, cascade ~10-16%, convention change ~25%) emerge from the model?

**Parameters:**
- Single pillar (strong tipping domain, small-world network, N=500)
- No inter-pillar connections
- Committed fraction: sweep from 0% to 30% in 0.5% increments
- Replications: 200 per condition

**Output:**
- For each committed fraction: mean equilibrium active fraction, standard deviation, time to equilibrium
- Plot: committed fraction (x-axis) vs. equilibrium active fraction (y-axis)
- Identify phase transition points: where does the curve show sharp transitions?
- Compare detected transition points to the three-threshold model predictions

#### Experiment 3: Network Density Effects

**Question:** Do dense networks tip at lower thresholds than sparse ones, consistent with Xie et al. (2011)?

**Parameters:**
- Single pillar, varying topology:
  - Small-world with avg degree 5, 10, 15, 20
  - Erdos-Renyi with avg degree 3, 5, 10, 15
  - Barabasi-Albert with m = 2, 3, 5, 8
- Committed fraction: sweep from 0% to 20% in 1% increments
- N = 500 for all conditions
- Replications: 100 per condition

**Output:**
- For each topology and committed fraction: mean equilibrium active fraction
- Plot: committed fraction vs. equilibrium activation, one curve per topology
- Report: critical fraction (the committed % at which the system transitions from <10% equilibrium to >50% equilibrium) for each topology

#### Experiment 4: Inter-Pillar Transmission Type Comparison

**Question:** How do the three transmission mechanisms (signaling, constraint removal, mechanical) compare in their effect on cascade propagation across pillars?

**Parameters:**
- 3 pillars (all strong tipping domains for comparability)
- Strategy: sequential, weakest-first
- Total committed fraction: 5% (to ensure the first pillar is at activation threshold)
- Vary transmission type between pillar 1 and pillar 2:
  - Condition A: signaling only (threshold reduction = 0.05)
  - Condition B: constraint removal (threshold reduction = 0.10 for top 30% agents)
  - Condition C: mechanical (replace 30% of pillar 2 agents with committed agents)
  - Condition D: no inter-pillar connection (control)
- Replications: 200 per condition

**Output:**
- Time to pillar 2 tipping for each condition
- Probability of pillar 2 tipping within 500 timesteps for each condition
- Plot: cascade propagation over time for each condition

#### Experiment 5: Counter-Mobilization Effects

**Question:** How do counter-mobilization strategies affect threshold dynamics?

**Parameters:**
- Single strong pillar (N=500, small-world)
- Committed fraction: 8% (near cascade threshold)
- Counter-mobilization conditions:
  - Baseline: no counter-mobilization
  - Fragmentation: split pillar into two disconnected subnetworks of 250
  - Atomization: randomly remove 30% of edges
  - Co-optation: raise thresholds by 0.15 for 20% of agents (simulating patronage)
  - Decapitation: remove top 5 opinion leaders (replace with regular agents)
  - Combined: atomization + co-optation (the most realistic adversarial condition)
- Replications: 200 per condition

**Output:**
- Equilibrium active fraction for each condition
- Time to cascade for conditions where cascade occurs
- Probability of cascade within 500 timesteps
- Plot: comparison across all conditions

---

### Implementation Notes

1. **Reproducibility:** Set random seed for each replication. Save seeds with output data.

2. **Performance:** With N=500 per pillar, 5 pillars, and 500 timesteps, each run processes ~1.25M agent-timestep evaluations. At 100-200 replications per condition, this is computationally manageable in pure Python with NetworkX. If performance becomes an issue, the inner loop (neighbor fraction calculation) can be vectorized with NumPy adjacency matrix operations.

3. **Validation:** Before running experiments, validate the single-pillar model against Xie et al.'s known result: on a complete graph of 100 agents, the critical fraction for committed-minority-driven consensus should be approximately 10%. If the model produces a critical fraction substantially different from this, the threshold distribution or activation dynamics need recalibration.

4. **Output format:** CSV files with one row per replication per condition. Columns: experiment_id, strategy, committed_fraction, pillar_id, topology, avg_degree, transmission_type, replication, seed, equilibrium_active_fraction, timesteps_to_cascade, pillars_tipped, total_active_fraction.

5. **Visualization:** Generate standard plots for each experiment automatically at the end of each run. Save as PNG to output directory.

---

### What the Model Does and Does Not Claim

**Does:** Test whether sequential pillar targeting produces better outcomes than alternative strategies in an agent-based model with realistic threshold distributions and multiple transmission mechanisms. Generate threshold band estimates. Test network density effects. Test counter-mobilization effects.

**Does not:** Prove that Sequential Tipping Theory is correct for real-world social systems. The model is a computational exploration, not an empirical validation. Real institutional dynamics are vastly more complex than any agent-based model can capture. The results should be framed as "consistent with" or "inconsistent with" the theory's predictions, not as proof.

**Relationship to Chenoweth et al. (2022):** Our model extends their ABM by adding structured pillar networks with distinct topologies, three transmission mechanisms, and threshold dynamics within each pillar. Their finding (pillar-focused > mass mobilization) is the baseline prediction. Our model tests whether this finding holds with more realistic network structure and whether the specific sequencing logic (which pillar to target first, how tipped pillars affect untipped ones) matters.

---

### Source References for Model Design

- Xie, J. et al. (2011). Social consensus through the influence of committed minorities. *Physical Review E*, 84(1), 011130. [Baseline threshold dynamics]
- Centola, D. et al. (2018). Experimental evidence for tipping points in social convention. *Science*, 360(6393), 1116-1119. [Convention-change threshold]
- Chenoweth, E., Hocking, A. & Marks, Z. (2022). A dynamic model of nonviolent resistance strategy. *PLoS ONE*, 17(7), e0269976. [Pillar-focused strategy ABM]
- Watts, D. J. (2002). A simple model of global cascades on random networks. *PNAS*, 99(9), 5766-5771. [Cascade dynamics on random networks]
- Macy, M. W. & Evtushenko, A. (2020). Threshold models of collective behavior II. *Sociological Science*, 7, 628-648. [Stochastic thresholds and predictability]
- Granovetter, M. (1978). Threshold models of collective behavior. *AJS*, 83(6), 1420-1443. [Foundational threshold model]
- Rogers, E. (2003). *Diffusion of Innovations* (5th ed.). Free Press. [Adopter category distribution]
