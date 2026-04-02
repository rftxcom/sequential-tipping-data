# Threshold Convergence Meta-Analysis: Specification Document

## For Implementation in Claude Code (Python)

### Purpose

Test whether independently derived threshold findings from the tipping point, diffusion, collective action, and network science literatures cluster in three bands (3-5%, 10-16%, 20-25%) more than chance would predict. Transform the convergence claim in the paper from a qualitative argument ("the ranges overlap and the methods differ, therefore the overlap is meaningful") to a quantitative demonstration.

---

### Phase 1: Dataset Construction

#### Data Collection

Compile every published finding that reports a critical fraction, tipping point, or threshold percentage for collective behavior change. Each finding becomes one row in the dataset.

**Inclusion criteria:**
- Reports a specific percentage (or percentage range) at which a qualitative change in collective behavior occurs
- The percentage refers to a fraction of a defined population (not an absolute number)
- The finding is based on empirical observation, computational simulation, controlled experiment, or formal theoretical derivation
- The finding is published in a peer-reviewed journal, academic book, or working paper from a recognized institution

**Exclusion criteria:**
- Findings that report absolute numbers rather than percentages
- Findings about individual behavior (not collective/population-level)
- Review articles that cite others' findings without original analysis
- Opinion pieces or non-empirical commentaries

#### Dataset Fields

```
finding_id: int
authors: string
year: int
source: string (journal/book)
threshold_value: float (central estimate, as percentage 0-100)
threshold_low: float (lower bound if range reported; same as threshold_value if point estimate)
threshold_high: float (upper bound if range reported; same as threshold_value if point estimate)
method: categorical [empirical, computational, experimental, theoretical]
domain: categorical [political_mobilization, opinion_dynamics, innovation_diffusion,
                     convention_change, organizational_change, other]
population_type: string (description: "national populations", "network agents",
                        "experimental groups", "farming communities", etc.)
population_scale: categorical [small (<100), medium (100-10000), large (>10000), variable]
what_measured: string (brief description: "peak campaign participation",
                      "committed fraction for opinion reversal", etc.)
notes: string
```

#### Known Findings to Include (Starting Dataset)

These are findings already identified in the paper. The dataset should be expanded through systematic literature search.

| ID | Authors | Year | Threshold | Method | Domain |
|----|---------|------|-----------|--------|--------|
| 1 | Chenoweth & Stephan | 2011 | 3.5% | empirical | political_mobilization |
| 2 | Lichbach | 1995 | 5.0% | theoretical | political_mobilization |
| 3 | Xie et al. | 2011 | 9.8% | computational | opinion_dynamics |
| 4 | Xie et al. (range low) | 2011 | 4.0% | computational | opinion_dynamics |
| 5 | Xie et al. (range high) | 2011 | 15.0% | computational | opinion_dynamics |
| 6 | Centola et al. | 2018 | 25.0% | experimental | convention_change |
| 7 | Iacopini et al. | 2022 | 0.3% | computational | convention_change |
| 8 | Rogers (innovator boundary) | 2003 | 2.5% | empirical | innovation_diffusion |
| 9 | Rogers (early adopter saturation) | 2003 | 16.0% | empirical | innovation_diffusion |
| 10 | Rogers (early majority saturation) | 2003 | 50.0% | empirical | innovation_diffusion |
| 11 | Moore (chasm) | 1991 | 16.0% | empirical | innovation_diffusion |
| 12 | Watts (cascade threshold) | 2002 | ~10-18% | computational | opinion_dynamics |

**Literature search strategy for expansion:**
Search Google Scholar, Web of Science, and Scopus for:
- "tipping point" AND ("critical fraction" OR "critical mass" OR "threshold" OR "committed minority")
- "social tipping" AND "threshold"
- "cascade" AND ("critical fraction" OR "minimum fraction")
- "collective action" AND "threshold" AND "percentage"
- "norm change" AND ("critical mass" OR "threshold")
- "diffusion" AND ("tipping point" OR "critical mass")

Target: 30-50 independent findings. Each finding from a different study or a different condition within the same study (e.g., different network topologies in Xie et al. count as separate findings).

---

### Phase 2: Statistical Analysis

#### Test 1: Three-Band Clustering

**Null hypothesis:** Threshold values are uniformly distributed across the 0-50% range (or follow some other non-clustered distribution).

**Alternative hypothesis:** Threshold values cluster in three bands centered approximately at 4%, 12%, and 25%.

**Method:**
1. Fit a Gaussian Mixture Model (GMM) with K=1, 2, 3, 4, and 5 components to the threshold values
2. Use BIC (Bayesian Information Criterion) to select the optimal number of clusters
3. If K=3 is selected, report the cluster centers and compare to the predicted bands (3-5%, 10-16%, ~25%)
4. If K != 3, report what K is selected and discuss implications

**Additional test:** Permutation test. Randomly shuffle the threshold values 10,000 times. For each permutation, fit K=3 GMM and record the cluster centers. Compare the observed cluster centers to the permutation distribution. If the observed centers fall at 4%, 12%, 25% more consistently than chance, report the p-value.

#### Test 2: Band Membership by Method Type

**Question:** Do findings cluster in the same bands regardless of method (empirical, computational, experimental)?

**Method:** Cross-tabulate findings by method type and band assignment (from the GMM clustering). Chi-squared test for independence. If the bands contain findings from multiple methods (not just one method per band), the convergence is cross-methodological, strengthening the claim.

#### Test 3: Comparison to Uniform Distribution

**Method:** Kolmogorov-Smirnov test comparing the observed threshold distribution to a uniform distribution on [0, 50]. Report the test statistic and p-value.

#### Test 4: Kernel Density Estimation

**Method:** Plot a kernel density estimate of the threshold values. Visually identify peaks. Compare peak locations to the three predicted bands. This provides a non-parametric complement to the GMM analysis.

---

### Phase 3: Visualization

1. **Histogram with GMM overlay:** Histogram of all threshold values (bins of 1%), with the fitted 3-component GMM curves overlaid. Color-code findings by method type.

2. **Strip plot by domain:** Each finding plotted as a point on a horizontal axis (0-50%), with vertical separation by domain (political, opinion dynamics, innovation diffusion, convention change, other). Shaded bands at 3-5%, 10-16%, 20-25% for visual comparison.

3. **KDE plot:** Kernel density estimate with peaks labeled.

4. **Forest plot:** Each finding as a point with error bars (threshold_low to threshold_high), ordered by threshold value. Shaded bands for reference.

---

### Phase 4: Output

Save all output to `~/projects/sequential-tipping-model/output/meta-analysis/`

Files:
- `threshold_findings_dataset.csv` — complete dataset
- `gmm_results.csv` — GMM fit statistics for K=1 through K=5
- `cluster_centers.csv` — centers and standard deviations for optimal K
- `permutation_test_results.csv` — permutation distribution of cluster centers
- `ks_test_results.txt` — Kolmogorov-Smirnov test output
- `histogram_gmm.png` — histogram with GMM overlay
- `strip_plot_by_domain.png` — strip plot
- `kde_plot.png` — kernel density estimate
- `forest_plot.png` — forest plot with error bars
- `summary_report.md` — narrative summary of all results

---

### What This Analysis Does and Does Not Claim

**Does:** Test whether the threshold values identified in independent studies cluster non-randomly and, if so, whether the clusters correspond to the three bands predicted by the Three-Threshold Model.

**Does not:** Prove that the threshold bands are universal constants. The analysis can demonstrate that clustering exists and that it is consistent with the model's predictions. It cannot prove that the clustering reflects a single underlying mechanism (that remains a theoretical argument, not a statistical one).

**Sensitivity:** The results will depend heavily on the dataset. A dataset of 15 findings dominated by the studies already cited in the paper will produce results that look like confirmation of the theory. A dataset of 40+ independently identified findings from a systematic literature search provides a much stronger test. The analysis should report results for both the "core" dataset (findings cited in the paper) and the "expanded" dataset (all findings from the literature search).

---

### Dependencies

- scikit-learn (GaussianMixture for GMM fitting)
- scipy (stats.kstest for K-S test, stats.chi2_contingency for chi-squared)
- matplotlib and seaborn (visualization)
- pandas (data management)
- numpy (numerical operations)
