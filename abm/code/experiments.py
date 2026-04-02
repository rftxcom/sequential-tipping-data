"""Experiment runners for the four core experiments."""

import os
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import pandas as pd

from .config import ModelConfig, ExperimentConfig, PillarConfig, CouplingConfig
from .model import Model, StepRecord, State
from .strategies import (SimultaneousStrategy, SequentialStrategy,
                         LeastLoyalFirstStrategy, RandomStrategy)
from .coupling import (no_coupling_config, cascade_only_config,
                        mixed_coupling_config, full_mixed_config,
                        measure_effective_threshold)
from .counter import (Fragmentation, Atomization, Cooptation, Decapitation,
                       DistributedLeadership, RedundantChannels, AlternativeInterdependence)


@dataclass
class ReplicationResult:
    c_fraction: float
    strategy: str
    system_tipped: bool
    final_defection_rate: float
    steps_to_equilibrium: int
    pillar_tipped: List[bool]
    pillar_final_rates: List[float]
    first_pillar_tip_step: Optional[int]
    cascade_start_step: Optional[int]
    all_tipped_step: Optional[int]


def _run_single_replication(args) -> ReplicationResult:
    """Worker function for parallel execution. Must be at module level for pickling."""
    config_dict, c_fraction, strategy_name, seed = args

    config = _reconstruct_config(config_dict)
    config.seed = seed

    total_pop = sum(p.size for p in config.pillars)
    total_committed = max(1, int(total_pop * c_fraction))

    model = Model(config)

    strategy = _make_strategy(strategy_name, model.rng)
    model.run_with_strategy(strategy, total_committed)

    history = model.history
    pillar_tipped = [p.tipped for p in model.pillars]
    pillar_rates = [p.defection_rate for p in model.pillars]
    system_tipped = model.total_defection_rate >= 0.50

    first_tip_step = None
    cascade_step = None
    all_tipped_step = None

    n_pillars = len(model.pillars)
    for record in history:
        tipped_count = sum(1 for r in record.pillar_defection_rates if r >= 0.50)
        if first_tip_step is None and tipped_count >= 1:
            first_tip_step = record.step
        if cascade_step is None and tipped_count >= 2:
            cascade_step = record.step
        if all_tipped_step is None and tipped_count == n_pillars:
            all_tipped_step = record.step

    return ReplicationResult(
        c_fraction=c_fraction,
        strategy=strategy_name,
        system_tipped=system_tipped,
        final_defection_rate=model.total_defection_rate,
        steps_to_equilibrium=len(history),
        pillar_tipped=pillar_tipped,
        pillar_final_rates=pillar_rates,
        first_pillar_tip_step=first_tip_step,
        cascade_start_step=cascade_step,
        all_tipped_step=all_tipped_step,
    )


def _config_to_dict(config: ModelConfig) -> dict:
    """Serialize ModelConfig for multiprocessing."""
    return {
        "pillars": [(p.name, p.size, p.topology, p.avg_degree,
                      p.threshold_mean, p.threshold_std,
                      p.opinion_leader_fraction, p.opinion_leader_multiplier)
                     for p in config.pillars],
        "couplings": [(c.source, c.target, c.coupling_type, c.strength)
                       for c in config.couplings],
        "coupling_trigger": config.coupling_trigger,
        "max_steps": config.max_steps,
        "equilibrium_window": config.equilibrium_window,
    }


def _reconstruct_config(d: dict) -> ModelConfig:
    """Deserialize ModelConfig from dict."""
    pillars = [PillarConfig(name=p[0], size=p[1], topology=p[2], avg_degree=p[3],
                            threshold_mean=p[4], threshold_std=p[5],
                            opinion_leader_fraction=p[6], opinion_leader_multiplier=p[7])
               for p in d["pillars"]]
    couplings = [CouplingConfig(source=c[0], target=c[1], coupling_type=c[2], strength=c[3])
                  for c in d["couplings"]]
    return ModelConfig(pillars=pillars, couplings=couplings,
                       coupling_trigger=d["coupling_trigger"],
                       max_steps=d["max_steps"],
                       equilibrium_window=d["equilibrium_window"])


def _make_strategy(name: str, rng=None):
    if name == "sequential":
        return SequentialStrategy()
    elif name == "simultaneous":
        return SimultaneousStrategy()
    elif name == "least_loyal_first":
        return LeastLoyalFirstStrategy()
    elif name == "random":
        return RandomStrategy(rng=rng)
    else:
        raise ValueError(f"Unknown strategy: {name}")


def run_experiment_1(exp_config: ExperimentConfig,
                     model_config: Optional[ModelConfig] = None,
                     results_dir: str = "results") -> pd.DataFrame:
    """Experiment 1: Sequential vs. Simultaneous.

    Vary C from 1-30%, compare strategies. Returns DataFrame with all results.
    """
    if model_config is None:
        model_config = ModelConfig.default()

    config_dict = _config_to_dict(model_config)
    c_range = exp_config.get_c_range()
    strategies = ["sequential", "simultaneous", "least_loyal_first"]

    tasks = []
    base_rng = np.random.default_rng(42)
    for c_frac in c_range:
        for strat in strategies:
            for rep in range(exp_config.n_replications):
                seed = int(base_rng.integers(2**31))
                tasks.append((config_dict, c_frac, strat, seed))

    print(f"Experiment 1: {len(tasks)} total runs "
          f"({len(c_range)} C values x {len(strategies)} strategies x {exp_config.n_replications} reps)")

    results = _run_parallel(tasks, exp_config.n_workers)
    df = _results_to_dataframe(results)

    os.makedirs(results_dir, exist_ok=True)
    df.to_csv(os.path.join(results_dir, "experiment_1_raw.csv"), index=False)

    # Summary: minimum C for system tipping per strategy
    summary = []
    for strat in strategies:
        strat_df = df[df["strategy"] == strat]
        for c_frac in c_range:
            c_df = strat_df[strat_df["c_fraction"] == c_frac]
            tip_rate = c_df["system_tipped"].mean()
            summary.append({
                "strategy": strat,
                "c_fraction": c_frac,
                "tip_probability": tip_rate,
                "mean_defection_rate": c_df["final_defection_rate"].mean(),
                "std_defection_rate": c_df["final_defection_rate"].std(),
            })
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(os.path.join(results_dir, "experiment_1_summary.csv"), index=False)

    print(f"Experiment 1 complete. Results in {results_dir}/")
    return df


def run_experiment_2(exp_config: ExperimentConfig,
                     model_config: Optional[ModelConfig] = None,
                     results_dir: str = "results") -> pd.DataFrame:
    """Experiment 2: Threshold Band Emergence.

    Slowly increase C, record three system-level thresholds.
    """
    if model_config is None:
        model_config = ModelConfig.default()

    config_dict = _config_to_dict(model_config)
    # Finer granularity for threshold detection
    c_range = [i * 0.005 for i in range(1, 61)]  # 0.5% to 30% in 0.5% steps

    tasks = []
    base_rng = np.random.default_rng(123)
    n_reps = min(exp_config.n_replications, 1000)  # Cap at 1000 as spec suggests
    for c_frac in c_range:
        for rep in range(n_reps):
            seed = int(base_rng.integers(2**31))
            tasks.append((config_dict, c_frac, "sequential", seed))

    print(f"Experiment 2: {len(tasks)} total runs "
          f"({len(c_range)} C values x {n_reps} reps)")

    results = _run_parallel(tasks, exp_config.n_workers)
    df = _results_to_dataframe(results)

    os.makedirs(results_dir, exist_ok=True)
    df.to_csv(os.path.join(results_dir, "experiment_2_raw.csv"), index=False)

    # Extract threshold bands
    threshold_data = []
    for c_frac in c_range:
        c_df = df[df["c_fraction"] == c_frac]
        threshold_data.append({
            "c_fraction": c_frac,
            "any_pillar_tipped_rate": c_df["first_pillar_tip_step"].notna().mean(),
            "cascade_started_rate": c_df["cascade_start_step"].notna().mean(),
            "all_tipped_rate": c_df["all_tipped_step"].notna().mean(),
            "mean_defection_rate": c_df["final_defection_rate"].mean(),
        })
    threshold_df = pd.DataFrame(threshold_data)
    threshold_df.to_csv(os.path.join(results_dir, "experiment_2_thresholds.csv"), index=False)

    # Find band boundaries (C at which each event occurs >50% of the time)
    activation_c = None
    cascade_c = None
    convention_c = None
    for row in threshold_data:
        if activation_c is None and row["any_pillar_tipped_rate"] >= 0.50:
            activation_c = row["c_fraction"]
        if cascade_c is None and row["cascade_started_rate"] >= 0.50:
            cascade_c = row["c_fraction"]
        if convention_c is None and row["all_tipped_rate"] >= 0.50:
            convention_c = row["c_fraction"]

    band_summary = {
        "activation_threshold": activation_c,
        "cascade_threshold": cascade_c,
        "convention_change_threshold": convention_c,
        "predicted_activation": "3.5-5%",
        "predicted_cascade": "10-16%",
        "predicted_convention": "~25%",
    }
    band_df = pd.DataFrame([band_summary])
    band_df.to_csv(os.path.join(results_dir, "experiment_2_bands.csv"), index=False)

    print(f"Experiment 2 complete.")
    print(f"  Activation threshold: {activation_c}")
    print(f"  Cascade threshold: {cascade_c}")
    print(f"  Convention change threshold: {convention_c}")
    return df


def run_experiment_3(exp_config: ExperimentConfig,
                     model_config: Optional[ModelConfig] = None,
                     results_dir: str = "results") -> pd.DataFrame:
    """Experiment 3: Inter-Pillar Leverage.

    Compare no coupling, cascade only, and mixed coupling.
    """
    if model_config is None:
        model_config = ModelConfig.default()

    scenarios = {
        "no_coupling": no_coupling_config(),
        "cascade_only": cascade_only_config(),
        "mixed": full_mixed_config(),
    }

    c_range = exp_config.get_c_range()
    all_results = []
    base_rng = np.random.default_rng(456)

    for scenario_name, couplings in scenarios.items():
        config = ModelConfig(
            pillars=model_config.pillars,
            couplings=couplings,
            coupling_trigger=model_config.coupling_trigger,
            max_steps=model_config.max_steps,
            equilibrium_window=model_config.equilibrium_window,
        )
        config_dict = _config_to_dict(config)

        tasks = []
        for c_frac in c_range:
            for rep in range(exp_config.n_replications):
                seed = int(base_rng.integers(2**31))
                tasks.append((config_dict, c_frac, "sequential", seed))

        print(f"Experiment 3 [{scenario_name}]: {len(tasks)} runs")
        results = _run_parallel(tasks, exp_config.n_workers)

        for r in results:
            all_results.append({
                "scenario": scenario_name,
                "c_fraction": r.c_fraction,
                "system_tipped": r.system_tipped,
                "final_defection_rate": r.final_defection_rate,
                "steps_to_equilibrium": r.steps_to_equilibrium,
            })

    df = pd.DataFrame(all_results)
    os.makedirs(results_dir, exist_ok=True)
    df.to_csv(os.path.join(results_dir, "experiment_3_raw.csv"), index=False)

    # Summary: min C for tipping per scenario
    summary = []
    for scenario in scenarios:
        s_df = df[df["scenario"] == scenario]
        for c_frac in c_range:
            c_df = s_df[s_df["c_fraction"] == c_frac]
            if len(c_df) > 0:
                summary.append({
                    "scenario": scenario,
                    "c_fraction": c_frac,
                    "tip_probability": c_df["system_tipped"].mean(),
                    "mean_defection_rate": c_df["final_defection_rate"].mean(),
                })
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(os.path.join(results_dir, "experiment_3_summary.csv"), index=False)

    print("Experiment 3 complete.")
    return df


def _run_exp4_single(args) -> dict:
    """Worker for Experiment 4 replications."""
    config_dict, c_fraction, counter_name, defense_name, seed = args

    config = _reconstruct_config(config_dict)
    config.seed = seed

    total_pop = sum(p.size for p in config.pillars)
    total_committed = max(1, int(total_pop * c_fraction))

    model = Model(config)
    rng = model.rng

    # Apply counter-strategy before running
    counter = _make_counter(counter_name)
    if counter is not None:
        # Apply to all pillars
        for i in range(len(model.pillars)):
            counter.apply(model, i, rng)

    # Apply defense after counter
    defense = _make_defense(defense_name)
    if defense is not None:
        defense.apply(model, rng)

    strategy = SequentialStrategy()
    model.run_with_strategy(strategy, total_committed)

    return {
        "c_fraction": c_fraction,
        "counter": counter_name or "none",
        "defense": defense_name or "none",
        "system_tipped": model.total_defection_rate >= 0.50,
        "final_defection_rate": model.total_defection_rate,
        "steps_to_equilibrium": len(model.history),
    }


def _make_counter(name):
    if name is None or name == "none":
        return None
    return {
        "fragmentation": Fragmentation(),
        "atomization": Atomization(),
        "cooptation": Cooptation(),
        "decapitation": Decapitation(),
    }.get(name)


def _make_defense(name):
    if name is None or name == "none":
        return None
    return {
        "distributed_leadership": DistributedLeadership(),
        "redundant_channels": RedundantChannels(),
        "alternative_interdependence": AlternativeInterdependence(),
    }.get(name)


def run_experiment_4(exp_config: ExperimentConfig,
                     model_config: Optional[ModelConfig] = None,
                     results_dir: str = "results") -> pd.DataFrame:
    """Experiment 4: Counter-Mobilization.

    Test counter-strategies and movement defenses.
    """
    if model_config is None:
        model_config = ModelConfig.default()

    config_dict = _config_to_dict(model_config)
    c_range = exp_config.get_c_range()

    counters = ["none", "fragmentation", "atomization", "cooptation", "decapitation"]
    defenses = ["none", "distributed_leadership", "redundant_channels", "alternative_interdependence"]

    # Test each counter alone, then each counter+defense pair
    test_pairs = [("none", "none")]  # Baseline
    for counter in counters[1:]:
        test_pairs.append((counter, "none"))  # Counter without defense
        for defense in defenses[1:]:
            test_pairs.append((counter, defense))  # Counter + defense

    tasks = []
    base_rng = np.random.default_rng(789)
    for c_frac in c_range:
        for counter, defense in test_pairs:
            for rep in range(exp_config.n_replications):
                seed = int(base_rng.integers(2**31))
                tasks.append((config_dict, c_frac, counter, defense, seed))

    print(f"Experiment 4: {len(tasks)} total runs")

    n_workers = exp_config.n_workers
    results = []
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(_run_exp4_single, t) for t in tasks]
        for i, future in enumerate(as_completed(futures)):
            results.append(future.result())
            if (i + 1) % 500 == 0:
                print(f"  {i + 1}/{len(tasks)} complete")

    df = pd.DataFrame(results)
    os.makedirs(results_dir, exist_ok=True)
    df.to_csv(os.path.join(results_dir, "experiment_4_raw.csv"), index=False)

    # Summary
    summary = []
    for counter, defense in test_pairs:
        pair_df = df[(df["counter"] == counter) & (df["defense"] == defense)]
        for c_frac in c_range:
            c_df = pair_df[pair_df["c_fraction"] == c_frac]
            if len(c_df) > 0:
                summary.append({
                    "counter": counter,
                    "defense": defense,
                    "c_fraction": c_frac,
                    "tip_probability": c_df["system_tipped"].mean(),
                    "mean_defection_rate": c_df["final_defection_rate"].mean(),
                })
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(os.path.join(results_dir, "experiment_4_summary.csv"), index=False)

    print("Experiment 4 complete.")
    return df


def _run_parallel(tasks, n_workers=None) -> List[ReplicationResult]:
    """Run replication tasks in parallel."""
    results = []
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(_run_single_replication, t) for t in tasks]
        for i, future in enumerate(as_completed(futures)):
            results.append(future.result())
            if (i + 1) % 500 == 0:
                print(f"  {i + 1}/{len(tasks)} complete")
    return results


def _results_to_dataframe(results: List[ReplicationResult]) -> pd.DataFrame:
    """Convert list of ReplicationResult to DataFrame."""
    rows = []
    for r in results:
        row = {
            "c_fraction": r.c_fraction,
            "strategy": r.strategy,
            "system_tipped": r.system_tipped,
            "final_defection_rate": r.final_defection_rate,
            "steps_to_equilibrium": r.steps_to_equilibrium,
            "first_pillar_tip_step": r.first_pillar_tip_step,
            "cascade_start_step": r.cascade_start_step,
            "all_tipped_step": r.all_tipped_step,
        }
        for i, (tipped, rate) in enumerate(zip(r.pillar_tipped, r.pillar_final_rates)):
            row[f"pillar_{i}_tipped"] = tipped
            row[f"pillar_{i}_rate"] = rate
        rows.append(row)
    return pd.DataFrame(rows)


def run_validation(results_dir: str = "results") -> pd.DataFrame:
    """Validate single-pillar dynamics against Xie et al. findings.

    Tests that critical committed fraction for cascade falls in 4-15% range
    for a single uncoupled pillar.
    """
    print("Running single-pillar validation...")

    # Test with different densities
    densities = [3, 6, 8, 10, 12]
    c_range = [i * 0.005 for i in range(1, 41)]  # 0.5% to 20%

    tasks = []
    base_rng = np.random.default_rng(999)

    for k in densities:
        config = ModelConfig(
            pillars=[PillarConfig("Test", 500, "erdos_renyi", k, 0.35, 0.15)],
            couplings=[],
            max_steps=500,
            equilibrium_window=10,
        )
        config_dict = _config_to_dict(config)

        for c_frac in c_range:
            for rep in range(100):
                seed = int(base_rng.integers(2**31))
                tasks.append((config_dict, c_frac, "simultaneous", seed))

    print(f"Validation: {len(tasks)} runs ({len(densities)} densities x {len(c_range)} C values x 100 reps)")

    results = _run_parallel(tasks)

    rows = []
    for r in results:
        rows.append({
            "c_fraction": r.c_fraction,
            "system_tipped": r.system_tipped,
            "final_defection_rate": r.final_defection_rate,
        })
    df = pd.DataFrame(rows)

    os.makedirs(results_dir, exist_ok=True)
    df.to_csv(os.path.join(results_dir, "validation_raw.csv"), index=False)

    # Find critical C for each density
    # (We need density info - reconstruct from task ordering)
    idx = 0
    validation_summary = []
    for k in densities:
        for c_frac in c_range:
            subset = df.iloc[idx:idx + 100]
            idx += 100
            tip_rate = subset["system_tipped"].mean()
            validation_summary.append({
                "avg_degree": k,
                "c_fraction": c_frac,
                "tip_probability": tip_rate,
                "mean_defection_rate": subset["final_defection_rate"].mean(),
            })

    val_df = pd.DataFrame(validation_summary)
    val_df.to_csv(os.path.join(results_dir, "validation_summary.csv"), index=False)

    # Report critical C per density
    print("\nValidation Results (Critical C for >50% tipping probability):")
    print(f"{'Density':>8} {'Critical C':>12} {'Xie Range':>12}")
    for k in densities:
        k_df = val_df[val_df["avg_degree"] == k]
        critical = k_df[k_df["tip_probability"] >= 0.50]
        if len(critical) > 0:
            c_val = critical["c_fraction"].min()
            print(f"{k:>8} {c_val:>11.1%} {'4-15%':>12}")
        else:
            print(f"{k:>8} {'> 20%':>12} {'4-15%':>12}")

    return df
