# Sequential Tipping: Data and Code Repository

Replication materials for:

Miller, D. (2026). Sequential Tipping: A Unified Theory of Movement Threshold Dynamics.

Contact: daniel@rftmedia.com
ORCID: [0009-0002-2923-6837](https://orcid.org/0009-0002-2923-6837)

---

## Overview

This repository contains all data, code, and analysis outputs for "Sequential Tipping: A Unified Theory of Movement Threshold Dynamics." It includes (1) a meta-analysis dataset of 30 threshold values from 22 studies spanning computational, empirical, and experimental methods (1957--2025), with statistical tests of three-band clustering; (2) a coupled-network agent-based model (ABM) with source code, configuration, and raw output for all four experiments plus validation; and (3) formal specifications for both the meta-analysis and ABM sufficient for independent reimplementation.

---

## Repository Structure

```
sequential-tipping-data/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── meta-analysis/
│   ├── threshold_dataset.csv          # 30 threshold values from 22 studies
│   ├── results_summary.md             # Full statistical test results
│   ├── sensitivity_results.csv        # Deduplication sensitivity comparison table
│   ├── sensitivity_summary.md         # Sensitivity analysis interpretation
│   └── figures/
│       ├── 00_master_figure.png       # Combined KDE + GMM + permutation results
│       ├── 01_kde_all.png             # Kernel density estimation, all 30 values
│       ├── 02_gmm_analysis.png        # Gaussian mixture model (k=1 through k=5)
│       ├── 03_permutation_test.png    # Permutation test null distribution
│       ├── 04_stratified_analysis.png # Method-stratified band clustering
│       ├── sensitivity_kde_comparison.png  # Overlaid KDE curves, all 4 versions
│       ├── sensitivity_version_a.png  # Canonical deduplication KDE + GMM
│       ├── sensitivity_version_b.png  # Lowest-value deduplication KDE + GMM
│       └── sensitivity_version_c.png  # Highest-value deduplication KDE + GMM
├── abm/
│   ├── model_specification.md         # Formal ABM specification document
│   ├── code/
│   │   ├── __init__.py                # Package init
│   │   ├── config.py                  # Default parameters and experiment configs
│   │   ├── model.py                   # Core model: Agent, Pillar, Model classes
│   │   ├── coupling.py                # Inter-pillar coupling mechanisms
│   │   ├── strategies.py              # Movement allocation strategies
│   │   ├── counter.py                 # Counter-mobilization strategies
│   │   ├── experiments.py             # Experiment runners with parallel execution
│   │   ├── analysis.py                # Statistical analysis and plotting
│   │   └── run.py                     # Main entry point with CLI interface
│   ├── results/
│   │   ├── RESULTS_SUMMARY.md         # Full narrative summary of all experiments
│   │   ├── experiment_1_summary.csv   # Exp 1: strategy comparison aggregates
│   │   ├── experiment_1_raw.csv       # Exp 1: all replications
│   │   ├── experiment_2_bands.csv     # Exp 2: threshold band boundaries
│   │   ├── experiment_2_thresholds.csv# Exp 2: observed thresholds per coupling
│   │   ├── experiment_2_raw.csv       # Exp 2: all replications
│   │   ├── experiment_3_summary.csv   # Exp 3: coupling scenario aggregates
│   │   ├── experiment_3_raw.csv       # Exp 3: all replications
│   │   ├── experiment_4_summary.csv   # Exp 4: counter-strategy aggregates
│   │   ├── experiment_4_raw.csv       # Exp 4: all replications
│   │   ├── validation_summary.csv     # Validation: single-pillar aggregates
│   │   └── validation_raw.csv         # Validation: all replications
│   └── figures/
│       ├── experiment_1_strategies.png # Sequential vs. simultaneous comparison
│       ├── experiment_2_threshold_bands.png # Three emergent threshold bands
│       ├── experiment_3_coupling.png   # Coupling effect on tipping thresholds
│       ├── experiment_4_counter.png    # Counter-strategy backfire effects
│       └── validation_single_pillar.png# Xie et al. validation results
└── specs/
    ├── sequential_tipping_model_specification.md  # ABM formal specification
    ├── meta_analysis_specification.md             # Meta-analysis protocol
    └── threshold_meta_analysis_specification.md   # Threshold dataset protocol
```

---

## Meta-Analysis Dataset

### Description

The file `meta-analysis/threshold_dataset.csv` contains 30 independently derived threshold values from 22 studies published between 1957 and 2025. Each row represents a single threshold finding with 12 columns:

| Column | Description |
|--------|-------------|
| `study_id` | Unique integer identifier (1--30) |
| `authors` | Study authors |
| `year` | Publication year |
| `journal` | Journal or publisher |
| `threshold_value` | Reported threshold as a proportion (0--1) |
| `threshold_type` | activation, cascade, or convention_change |
| `method` | computational, empirical, experimental, or theoretical |
| `domain` | Subject domain (social, network_science, political, technological) |
| `population_type` | national, sub-national, computational, experimental_group |
| `network_structure` | Network topology (complete, random, scale_free, lattice, etc.) |
| `sample_or_model_size` | Sample size or number of agents |
| `notes` | Description of the specific finding |

### Supplementary Table: All 30 Threshold Entries

| ID | Authors | Year | Threshold | Method |
|----|---------|------|-----------|--------|
| 1 | Chenoweth & Stephan | 2011 | 3.5% | empirical |
| 2 | Lichbach | 1995 | 5.0% | theoretical |
| 3 | Xie et al. | 2011 | 9.8% | computational |
| 4 | Xie et al. (sparse ER) | 2011 | 4.0% | computational |
| 5 | Xie et al. (dense SF) | 2013 | 15.0% | computational |
| 6 | Centola et al. | 2018 | 25.0% | experimental |
| 7 | Iacopini et al. | 2022 | 0.3% | computational |
| 8 | Rogers | 2003 | 16.0% | empirical |
| 9 | Watts | 2002 | 18.0% | computational |
| 10 | Schelling | 1971 | 33.0% | computational |
| 11 | Singh et al. | 2012 | 10.0% | computational |
| 12 | Andreoni et al. | 2021 | 25.0% | experimental |
| 13 | Card, Mas & Rothstein (Chicago) | 2008 | 5.0% | empirical |
| 14 | Card, Mas & Rothstein (avg) | 2008 | 13.0% | empirical |
| 15 | Card, Mas & Rothstein (tolerant) | 2008 | 20.0% | empirical |
| 16 | Gleeson & Cahalane | 2007 | 3.5% | computational |
| 17 | Doyle et al. | 2013 | 5.0% | computational |
| 18 | Zhang, Lim & Szymanski | 2012 | 12.0% | theoretical |
| 19 | Andor et al. | 2022 | 30.0% | empirical |
| 20 | Grodzins | 1957 | 20.0% | empirical |
| 21 | Everall et al. (modeling) | 2025 | 24.0% | computational |
| 22 | Everall et al. (empirical) | 2025 | 27.0% | empirical |
| 23 | Xie et al. (BA network) | 2011 | 10.0% | computational |
| 24 | Wiedermann et al. | 2020 | 10.0% | computational |
| 25 | Doyle et al. (no crisis) | 2013 | 10.0% | computational |
| 26 | Centola (clustered) | 2010 | 14.0% | experimental |
| 27 | Sharpe & Lenton | 2021 | 5.0% | empirical |
| 28 | Lohmann (Leipzig peak) | 1994 | 20.0% | empirical |
| 29 | Oliver & Marwell | 1993 | 5.0% | computational |
| 30 | Xie et al. (competing) | 2012 | 10.0% | computational |

### Key Results

- **86.7%** of values (26/30) fall within the three predicted bands: activation (3--5%), cascade (10--16%), convention change (20--30%)
- Permutation test: **p < 0.0001** (0 of 10,000 random draws matched or exceeded observed clustering)
- Hartigan's dip test rejects unimodality: **p = 0.020**
- GMM best fit at k=3 yields component means of **4.1%, 10.0%, 20.3%**, aligning closely with predicted band centers
- Method-stratified analysis confirms the pattern holds independently across computational (p = 0.004), empirical (p < 0.0001), and experimental (p = 0.048) studies

Full statistical results are in `meta-analysis/results_summary.md`.

---

## Sensitivity Analysis

Three within-study deduplication strategies were applied to test robustness against non-independence (retaining one entry per research group, reducing N from 30 to 22):

| Version | Strategy | % in Bands | Permutation p | Dip p | Best k (BIC) | k=3 Means |
|---------|----------|-----------|--------------|-------|-------------|-----------|
| Full | All 30 entries | 86.7% | <0.0001 | 0.020 | 4 | 4.1%, 10.0%, 20.3% |
| A | Canonical (most-cited) | 81.8% | <0.0001 | 0.177 | 1 | 3.7%, 11.0%, 22.6% |
| B | Lowest threshold | 86.4% | <0.0001 | 0.719 | 2 | 4.5%, 16.4%, 31.8% |
| C | Highest threshold | 86.4% | <0.0001 | 0.223 | 1 | 3.7%, 15.0%, 27.8% |

The permutation test (the confirmatory test of the specific three-band prediction) remains highly significant (p < 0.0001) under all deduplication strategies. The dip test and GMM model selection lose significance at N=22 due to insufficient power for unsupervised mode detection, not absence of structure. Full interpretation is in `meta-analysis/sensitivity_summary.md`.

---

## Agent-Based Model

### Architecture

The ABM implements 5 coupled institutional networks (pillars) with Granovetter/Xie threshold dynamics. Each pillar is a small-world network of agents with individual defection thresholds drawn from a normal distribution. A committed minority ("the movement") recruits agents over 20 time steps according to one of several allocation strategies.

**Key components:**
- **5 pillars:** Military (200 agents), Legislature (300), Judiciary (150), Business (500), Religious (100) -- total 1,250 agents
- **Threshold dynamics:** Agents defect when the fraction of defected neighbors exceeds their individual threshold
- **3 coupling mechanisms:** Cascade (defection in one pillar directly influences neighbors in another), Mechanical (tipping one pillar shifts thresholds in coupled pillars), Bridge (agents with connections across pillars transmit influence)
- **100 replications** per parameter combination; 31 committed-minority (C) values tested from 1% to 30%

### Experiments

| Experiment | Tests | Data Files | Figure |
|-----------|-------|------------|--------|
| **Validation** | Single-pillar dynamics against Xie et al. (2011) | `validation_summary.csv`, `validation_raw.csv` | `validation_single_pillar.png` |
| **1. Sequential vs. Simultaneous** | Whether concentrating recruitment on one pillar at a time outperforms spreading it across all pillars | `experiment_1_summary.csv`, `experiment_1_raw.csv` | `experiment_1_strategies.png` |
| **2. Threshold Bands** | Whether three distinct system-level thresholds emerge from coupled network dynamics | `experiment_2_bands.csv`, `experiment_2_thresholds.csv`, `experiment_2_raw.csv` | `experiment_2_threshold_bands.png` |
| **3. Coupling Effects** | Whether inter-pillar coupling reduces the committed minority required for system tipping | `experiment_3_summary.csv`, `experiment_3_raw.csv` | `experiment_3_coupling.png` |
| **4. Counter-Mobilization** | Whether regime counter-strategies raise or lower the tipping threshold | `experiment_4_summary.csv`, `experiment_4_raw.csv` | `experiment_4_counter.png` |

### Key Results

- **Sequential targeting requires 44% fewer agents** than simultaneous (4.9% vs. 8.7% committed minority)
- **Mixed coupling reduces the threshold by 67%** (8.7% with no coupling to 2.9% with cascade + mechanical + bridge)
- **Optimal first target** is the pillar with the strongest outgoing coupling connections, not the easiest to tip
- **Three of four counter-strategies backfire:** fragmentation, atomization, and decapitation reduce the tipping threshold by 41% by degrading the social fabric that maintains institutional loyalty

Full narrative results are in `abm/results/RESULTS_SUMMARY.md`.

---

## Reproducing Results

### Requirements

Python 3.10+ with the following packages:

```
networkx
numpy
matplotlib
pandas
scipy
scikit-learn
```

Install with:

```bash
pip install networkx numpy matplotlib pandas scipy scikit-learn
```

### Running the ABM

From the repository root:

```bash
# Quick test (~30 seconds)
python -m abm.code.run --experiment 1 --quick

# Full run with 100 replications (~27 minutes total)
python -m abm.code.run --experiment all --reps 100

# Validation only
python -m abm.code.run --validate

# Regenerate plots from existing data
python -m abm.code.run --plot-only --experiment all
```

Or copy the `abm/code/` directory to a standalone location and run as:

```bash
python -m sequential_tipping_model.run --experiment all --reps 100
```

See `abm/model_specification.md` for the full formal specification, including all parameters, coupling matrices, and threshold distributions. The specification is sufficient for independent reimplementation in any language.

### Running the Meta-Analysis

The meta-analysis statistical tests (KDE, GMM, dip test, permutation test, method stratification) were implemented in the Python scripts that produced the output in `meta-analysis/`. The dataset (`threshold_dataset.csv`) and the analysis specification (`specs/meta_analysis_specification.md`) are sufficient to reproduce all statistical tests independently. Key parameters:

- Permutation test: 10,000 random draws from Uniform(0, 0.5)
- GMM: k=1 through k=5, BIC model selection
- Dip test: Hartigan's dip statistic
- Band definitions: activation [0.03, 0.05], cascade [0.10, 0.16], convention change [0.20, 0.30]

---

## License

This work is released under the [MIT License](LICENSE).

---

## Citation

```bibtex
@article{miller2026sequential,
  title={Sequential Tipping: A Unified Theory of Movement Threshold Dynamics},
  author={Miller, Daniel},
  year={2026}
}
```
