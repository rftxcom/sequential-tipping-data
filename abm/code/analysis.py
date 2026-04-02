"""Statistical analysis and plotting for experiment results."""

import os
from typing import Optional
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick


def set_style():
    """Set consistent plot style."""
    plt.rcParams.update({
        "figure.figsize": (10, 6),
        "figure.dpi": 150,
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "legend.fontsize": 10,
        "lines.linewidth": 2,
        "axes.grid": True,
        "grid.alpha": 0.3,
    })


def plot_experiment_1(results_dir: str = "results"):
    """Plot Experiment 1: Sequential vs. Simultaneous."""
    set_style()
    summary = pd.read_csv(os.path.join(results_dir, "experiment_1_summary.csv"))

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Panel A: Tipping probability vs C
    ax = axes[0]
    colors = {"sequential": "#2196F3", "simultaneous": "#F44336", "least_loyal_first": "#4CAF50"}
    labels = {"sequential": "Sequential", "simultaneous": "Simultaneous",
              "least_loyal_first": "Least-Loyal-First"}

    for strat in ["sequential", "simultaneous", "least_loyal_first"]:
        s_df = summary[summary["strategy"] == strat]
        ax.plot(s_df["c_fraction"] * 100, s_df["tip_probability"],
                color=colors[strat], label=labels[strat])

    ax.set_xlabel("Committed Minority (% of total population)")
    ax.set_ylabel("System Tipping Probability")
    ax.set_title("A. Tipping Probability by Strategy")
    ax.legend()
    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1.05)

    # Panel B: Mean defection rate vs C
    ax = axes[1]
    for strat in ["sequential", "simultaneous", "least_loyal_first"]:
        s_df = summary[summary["strategy"] == strat]
        ax.plot(s_df["c_fraction"] * 100, s_df["mean_defection_rate"],
                color=colors[strat], label=labels[strat])
        ax.fill_between(s_df["c_fraction"] * 100,
                         s_df["mean_defection_rate"] - s_df["std_defection_rate"],
                         s_df["mean_defection_rate"] + s_df["std_defection_rate"],
                         color=colors[strat], alpha=0.15)

    ax.set_xlabel("Committed Minority (% of total population)")
    ax.set_ylabel("Mean System Defection Rate")
    ax.set_title("B. Defection Rate by Strategy")
    ax.legend()
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1.05)

    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "experiment_1_strategies.png"), bbox_inches="tight")
    plt.close()

    # Find and report minimum C for each strategy
    print("\n--- Experiment 1 Results ---")
    for strat in ["sequential", "simultaneous", "least_loyal_first"]:
        s_df = summary[summary["strategy"] == strat]
        above_50 = s_df[s_df["tip_probability"] >= 0.50]
        if len(above_50) > 0:
            min_c = above_50["c_fraction"].min()
            print(f"  {labels[strat]:>20s}: min C for tipping = {min_c:.1%}")
        else:
            print(f"  {labels[strat]:>20s}: did not reach tipping in tested range")


def plot_experiment_2(results_dir: str = "results"):
    """Plot Experiment 2: Threshold Band Emergence."""
    set_style()
    thresholds = pd.read_csv(os.path.join(results_dir, "experiment_2_thresholds.csv"))
    bands = pd.read_csv(os.path.join(results_dir, "experiment_2_bands.csv"))

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(thresholds["c_fraction"] * 100, thresholds["any_pillar_tipped_rate"],
            color="#FF9800", label="First Pillar Tips (Activation)", linewidth=2.5)
    ax.plot(thresholds["c_fraction"] * 100, thresholds["cascade_started_rate"],
            color="#F44336", label="Cascade Begins (2+ pillars)", linewidth=2.5)
    ax.plot(thresholds["c_fraction"] * 100, thresholds["all_tipped_rate"],
            color="#9C27B0", label="All Pillars Tip (Convention Change)", linewidth=2.5)

    # Shade predicted bands
    ax.axvspan(3.5, 5, alpha=0.15, color="#FF9800", label="Predicted Activation (3.5-5%)")
    ax.axvspan(10, 16, alpha=0.15, color="#F44336", label="Predicted Cascade (10-16%)")
    ax.axvspan(23, 27, alpha=0.15, color="#9C27B0", label="Predicted Convention (~25%)")

    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5, label="50% probability line")

    ax.set_xlabel("Committed Minority (% of total population)")
    ax.set_ylabel("Probability of Event Occurring")
    ax.set_title("Threshold Band Emergence from Coupled Network Dynamics")
    ax.legend(loc="center right", fontsize=9)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1.05)

    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "experiment_2_threshold_bands.png"), bbox_inches="tight")
    plt.close()

    # Report
    print("\n--- Experiment 2 Results ---")
    for _, row in bands.iterrows():
        a = row.get("activation_threshold")
        c = row.get("cascade_threshold")
        v = row.get("convention_change_threshold")
        print(f"  Activation threshold:        {a if pd.notna(a) else 'not reached'}"
              f" (predicted: {row['predicted_activation']})")
        print(f"  Cascade threshold:           {c if pd.notna(c) else 'not reached'}"
              f" (predicted: {row['predicted_cascade']})")
        print(f"  Convention change threshold: {v if pd.notna(v) else 'not reached'}"
              f" (predicted: {row['predicted_convention']})")


def plot_experiment_3(results_dir: str = "results"):
    """Plot Experiment 3: Inter-Pillar Leverage."""
    set_style()
    summary = pd.read_csv(os.path.join(results_dir, "experiment_3_summary.csv"))

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    colors = {"no_coupling": "#9E9E9E", "cascade_only": "#2196F3", "mixed": "#E91E63"}
    labels = {"no_coupling": "No Coupling", "cascade_only": "Cascade Only",
              "mixed": "Mixed (Cascade + Mechanical + Bridge)"}

    # Panel A: Tipping probability
    ax = axes[0]
    for scenario in ["no_coupling", "cascade_only", "mixed"]:
        s_df = summary[summary["scenario"] == scenario]
        ax.plot(s_df["c_fraction"] * 100, s_df["tip_probability"],
                color=colors[scenario], label=labels[scenario])

    ax.set_xlabel("Committed Minority (% of total population)")
    ax.set_ylabel("System Tipping Probability")
    ax.set_title("A. Coupling Effect on Tipping Probability")
    ax.legend()
    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1.05)

    # Panel B: Mean defection rate
    ax = axes[1]
    for scenario in ["no_coupling", "cascade_only", "mixed"]:
        s_df = summary[summary["scenario"] == scenario]
        ax.plot(s_df["c_fraction"] * 100, s_df["mean_defection_rate"],
                color=colors[scenario], label=labels[scenario])

    ax.set_xlabel("Committed Minority (% of total population)")
    ax.set_ylabel("Mean System Defection Rate")
    ax.set_title("B. Coupling Effect on Defection Rate")
    ax.legend()
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1.05)

    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "experiment_3_coupling.png"), bbox_inches="tight")
    plt.close()

    # Report minimum C per scenario
    print("\n--- Experiment 3 Results ---")
    for scenario in ["no_coupling", "cascade_only", "mixed"]:
        s_df = summary[summary["scenario"] == scenario]
        above_50 = s_df[s_df["tip_probability"] >= 0.50]
        if len(above_50) > 0:
            min_c = above_50["c_fraction"].min()
            print(f"  {labels[scenario]:>40s}: min C = {min_c:.1%}")
        else:
            print(f"  {labels[scenario]:>40s}: did not reach tipping")


def plot_experiment_4(results_dir: str = "results"):
    """Plot Experiment 4: Counter-Mobilization."""
    set_style()
    summary = pd.read_csv(os.path.join(results_dir, "experiment_4_summary.csv"))

    # Panel A: Counter-strategies without defense
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    counters_colors = {
        "none": "#4CAF50",
        "fragmentation": "#F44336",
        "atomization": "#FF9800",
        "cooptation": "#9C27B0",
        "decapitation": "#795548",
    }
    counter_labels = {
        "none": "Baseline (No Counter)",
        "fragmentation": "Fragmentation",
        "atomization": "Atomization",
        "cooptation": "Co-optation",
        "decapitation": "Decapitation",
    }

    ax = axes[0]
    no_defense = summary[summary["defense"] == "none"]
    for counter in counters_colors:
        c_df = no_defense[no_defense["counter"] == counter]
        if len(c_df) > 0:
            ax.plot(c_df["c_fraction"] * 100, c_df["tip_probability"],
                    color=counters_colors[counter], label=counter_labels[counter])

    ax.set_xlabel("Committed Minority (%)")
    ax.set_ylabel("System Tipping Probability")
    ax.set_title("A. Counter-Strategies (No Defense)")
    ax.legend(fontsize=9)
    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1.05)

    # Panel B: Decapitation with and without distributed leadership defense
    ax = axes[1]
    baseline = summary[(summary["counter"] == "none") & (summary["defense"] == "none")]
    decap_no_def = summary[(summary["counter"] == "decapitation") & (summary["defense"] == "none")]
    decap_w_def = summary[(summary["counter"] == "decapitation") &
                           (summary["defense"] == "distributed_leadership")]

    ax.plot(baseline["c_fraction"] * 100, baseline["tip_probability"],
            color="#4CAF50", label="Baseline")
    if len(decap_no_def) > 0:
        ax.plot(decap_no_def["c_fraction"] * 100, decap_no_def["tip_probability"],
                color="#F44336", label="Decapitation (no defense)")
    if len(decap_w_def) > 0:
        ax.plot(decap_w_def["c_fraction"] * 100, decap_w_def["tip_probability"],
                color="#2196F3", label="Decapitation + Distributed Leadership")

    ax.set_xlabel("Committed Minority (%)")
    ax.set_ylabel("System Tipping Probability")
    ax.set_title("B. Defense Effectiveness (Decapitation Example)")
    ax.legend(fontsize=9)
    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1.05)

    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "experiment_4_counter.png"), bbox_inches="tight")
    plt.close()

    # Report
    print("\n--- Experiment 4 Results ---")
    no_def = summary[summary["defense"] == "none"]
    for counter in counters_colors:
        c_df = no_def[no_def["counter"] == counter]
        above_50 = c_df[c_df["tip_probability"] >= 0.50]
        if len(above_50) > 0:
            min_c = above_50["c_fraction"].min()
            print(f"  {counter_labels[counter]:>30s}: min C = {min_c:.1%}")
        else:
            print(f"  {counter_labels[counter]:>30s}: did not reach tipping")


def plot_validation(results_dir: str = "results"):
    """Plot validation results."""
    set_style()
    val_summary = pd.read_csv(os.path.join(results_dir, "validation_summary.csv"))

    fig, ax = plt.subplots(figsize=(10, 6))

    densities = sorted(val_summary["avg_degree"].unique())
    cmap = plt.cm.viridis(np.linspace(0.2, 0.9, len(densities)))

    for i, k in enumerate(densities):
        k_df = val_summary[val_summary["avg_degree"] == k]
        ax.plot(k_df["c_fraction"] * 100, k_df["tip_probability"],
                color=cmap[i], label=f"k={k}")

    # Shade Xie et al. range
    ax.axvspan(4, 15, alpha=0.15, color="green", label="Xie et al. range (4-15%)")
    ax.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)

    ax.set_xlabel("Committed Minority (% of pillar population)")
    ax.set_ylabel("Tipping Probability")
    ax.set_title("Single-Pillar Validation Against Xie et al. (2011)")
    ax.legend()
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 1.05)

    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "validation_single_pillar.png"), bbox_inches="tight")
    plt.close()


def generate_summary_table(results_dir: str = "results"):
    """Generate a final summary table comparing all experiment results."""
    print("\n" + "=" * 70)
    print("SEQUENTIAL TIPPING MODEL: RESULTS SUMMARY")
    print("=" * 70)

    # Experiment 1
    try:
        exp1 = pd.read_csv(os.path.join(results_dir, "experiment_1_summary.csv"))
        print("\nPrediction 1: Sequential targeting outperforms simultaneous")
        print("-" * 50)
        for strat in ["sequential", "simultaneous", "least_loyal_first"]:
            s_df = exp1[exp1["strategy"] == strat]
            above_50 = s_df[s_df["tip_probability"] >= 0.50]
            if len(above_50) > 0:
                min_c = above_50["c_fraction"].min()
                print(f"  {strat:>20s}: {min_c:.1%}")
            else:
                print(f"  {strat:>20s}: > {s_df['c_fraction'].max():.1%}")

        seq_c = exp1[exp1["strategy"] == "sequential"]
        sim_c = exp1[exp1["strategy"] == "simultaneous"]
        seq_min = seq_c[seq_c["tip_probability"] >= 0.50]["c_fraction"].min() if len(seq_c[seq_c["tip_probability"] >= 0.50]) > 0 else None
        sim_min = sim_c[sim_c["tip_probability"] >= 0.50]["c_fraction"].min() if len(sim_c[sim_c["tip_probability"] >= 0.50]) > 0 else None

        if seq_min is not None and sim_min is not None:
            if seq_min < sim_min:
                print(f"  SUPPORTED: Sequential ({seq_min:.1%}) < Simultaneous ({sim_min:.1%})")
            else:
                print(f"  NOT SUPPORTED: Sequential ({seq_min:.1%}) >= Simultaneous ({sim_min:.1%})")
        else:
            print("  INCONCLUSIVE: insufficient data")
    except FileNotFoundError:
        print("\nExperiment 1: not yet run")

    # Experiment 2
    try:
        bands = pd.read_csv(os.path.join(results_dir, "experiment_2_bands.csv"))
        print("\nPrediction 2: Three threshold bands emerge")
        print("-" * 50)
        for _, row in bands.iterrows():
            for label, key, pred in [
                ("Activation", "activation_threshold", "3.5-5%"),
                ("Cascade", "cascade_threshold", "10-16%"),
                ("Convention", "convention_change_threshold", "~25%"),
            ]:
                val = row.get(key)
                if pd.notna(val):
                    print(f"  {label:>15s}: {float(val):.1%} (predicted: {pred})")
                else:
                    print(f"  {label:>15s}: not reached (predicted: {pred})")
    except FileNotFoundError:
        print("\nExperiment 2: not yet run")

    # Experiment 3
    try:
        exp3 = pd.read_csv(os.path.join(results_dir, "experiment_3_summary.csv"))
        print("\nPrediction 3: Inter-pillar coupling reduces effective thresholds")
        print("-" * 50)
        for scenario in ["no_coupling", "cascade_only", "mixed"]:
            s_df = exp3[exp3["scenario"] == scenario]
            above_50 = s_df[s_df["tip_probability"] >= 0.50]
            if len(above_50) > 0:
                min_c = above_50["c_fraction"].min()
                print(f"  {scenario:>15s}: {min_c:.1%}")
            else:
                print(f"  {scenario:>15s}: > {s_df['c_fraction'].max():.1%}")
    except FileNotFoundError:
        print("\nExperiment 3: not yet run")

    print("\n" + "=" * 70)
