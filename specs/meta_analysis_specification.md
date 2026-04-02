# Meta-Analytic Convergence Test: Specification Document

## For Implementation in Claude Code (Python)

### Purpose

Compile all published threshold findings from the tipping point, diffusion, collective action, and network science literatures. Test whether the distribution of reported threshold values clusters in three bands (3.5-5%, 10-16%, ~25%) significantly more than chance would predict. Transform the convergence claim from a qualitative pattern observation to a quantitative statistical demonstration.

---

### Data Collection

#### Inclusion Criteria

A study is included if it:
1. Reports a specific numerical threshold (percentage of a population or network) at which a phase transition, cascade, or adoption inflection occurs
2. Uses one of: empirical data analysis, computational simulation, controlled experiment, or theoretical derivation
3. Measures a social process: innovation adoption, political mobilization, opinion dynamics, norm/convention change, collective action, or institutional defection
4. Is published in a peer-reviewed journal, academic book, or working paper from a recognized institution

A study is excluded if it:
1. Reports a threshold for non-social processes (epidemiological, biological, physical)
2. Reports only a qualitative description of tipping without a specific numerical value
3. Is a secondary citation of another included study's finding (to avoid double-counting)

#### Coding Schema

For each included finding, code:

| Field | Description | Values |
|-------|-------------|--------|
| `study_id` | Unique identifier | String |
| `authors` | Author(s) | String |
| `year` | Publication year | Integer |
| `journal` | Publication venue | String |
| `threshold_pct` | Reported threshold as percentage | Float (0-100) |
| `threshold_lower` | Lower bound if a range is reported | Float or null |
| `threshold_upper` | Upper bound if a range is reported | Float or null |
| `method` | Research method | "empirical", "computational", "experimental", "theoretical" |
| `domain` | Subject domain | "political", "innovation", "opinion", "convention", "collective_action", "institutional" |
| `process` | What is being measured | Free text (e.g., "peak participation for campaign success", "opinion reversal in binary model") |
| `population_type` | Type of population studied | "national", "subnational", "organizational", "experimental_group", "computational_network" |
| `network_topology` | If computational, what network type | "complete", "random", "scale-free", "small-world", "lattice", "empirical", "NA" |
| `n_observations` | Number of observations/trials/simulations | Integer or null |
| `notes` | Qualifications, caveats | Free text |

#### Known Studies to Include (Starting List)

These are confirmed from the paper's existing sources. Research should expand this list to 30-50+ findings.

| Study | Threshold | Method | Domain |
|-------|-----------|--------|--------|
| Chenoweth & Stephan (2011) | 3.5% | Empirical (323 campaigns) | Political |
| Lichbach (1995) | 5% | Theoretical | Collective action |
| Xie et al. (2011) — complete graph | 9.8% | Computational | Opinion |
| Xie et al. (2011) — sparse networks | 4% | Computational | Opinion |
| Xie et al. (2013) — CDMM model | <5% | Computational | Opinion |
| Xie et al. (2013) — range across models | 4-15% | Computational | Opinion |
| Centola et al. (2018) | 25% | Experimental | Convention |
| Iacopini et al. (2022) — group interactions | 0.3-10% | Computational | Convention |
| Rogers (2003) — innovator boundary | 2.5% | Empirical (5200+ studies) | Innovation |
| Rogers (2003) — early adopter boundary | 16% | Empirical | Innovation |
| Watts (2002) — cascade threshold on random networks | varies with connectivity | Computational | Opinion |
| Wiedermann et al. (2020) — tipping threshold | varies with network structure | Computational | Collective action |

#### Research Targets for Expansion

Claude Code should search for additional threshold findings in:

1. **Diffusion literature post-Rogers:** Studies that measured specific adoption inflection points in technology, medical practice, agricultural practice, or organizational change. Look for: Bass diffusion model studies, Moore's "chasm" empirical tests, Valente (1996) network threshold extensions.

2. **Committed minority models:** Extensions of Xie et al. Look for: Naming Game variants, voter model variants, majority-rule model variants, Sznajd model variants. Each may report a critical committed fraction.

3. **Experimental social psychology:** Extensions of Centola. Look for: convention-change experiments with different group sizes, different incentive structures, different communication networks. Centola's own lab has published follow-up work.

4. **Collective action / revolution literature:** Extensions of Chenoweth. Look for: Lichbach extensions, critical mass studies (Oliver & Marwell), Kuran (1991) preference falsification thresholds, Lohmann (1994) information cascade thresholds.

5. **Network cascade literature:** Extensions of Watts (2002). Look for: cascade threshold studies on different network topologies, multiplex networks, temporal networks.

6. **Organizational change literature:** Studies measuring the critical fraction of adopters needed for organizational transformation (new practices in hospitals, schools, firms).

**Search strategy for Claude Code:**
- Google Scholar queries: "critical mass" + "threshold" + "percent" + [domain keyword]
- "tipping point" + "committed minority" + specific percentage
- "cascade threshold" + "social network"
- Check reference lists of Xie et al. (2011), Centola et al. (2018), and Wiedermann et al. (2020) for additional threshold studies
- Check citing articles of these key papers for newer findings

---

### Statistical Analysis

#### Test 1: Band Clustering

**Null hypothesis:** Reported threshold values are uniformly distributed across the 0-50% range (or follow some other non-banded distribution such as a single normal distribution).

**Alternative hypothesis:** Reported threshold values cluster in three bands centered approximately at 4%, 12%, and 25%.

**Method:**
1. Kernel density estimation of the threshold distribution
2. Gaussian mixture model (GMM) with k=1,2,3,4,5 components. Use BIC/AIC to determine optimal k. If k=3 is optimal, report the band centers and widths.
3. Permutation test: randomly shuffle threshold values across studies 10,000 times. For each permutation, compute the within-cluster sum of squares for a 3-cluster k-means solution. Compare the observed WCSS to the permutation distribution. If the observed clustering is tighter than 95% of permutations, reject the null.

#### Test 2: Method Independence

**Hypothesis:** The clustering pattern holds across research methods. If the bands are methodological artifacts, they should appear only within specific method types.

**Method:**
1. Separate the findings by method (empirical, computational, experimental, theoretical)
2. Within each method category, test whether the threshold distribution shows the same 3-band pattern
3. Cross-method analysis: for each band, do findings from at least 2 different method types contribute? If so, the banding is not a method artifact.

#### Test 3: Domain Independence

**Hypothesis:** The clustering pattern holds across domains (political, innovation, opinion, convention).

**Method:** Same as Test 2, but stratified by domain rather than method.

#### Test 4: Publication Bias Assessment

**Method:** Funnel plot of threshold value vs. sample size / precision. Look for asymmetry that would suggest small-study effects or selective reporting. This is important because if researchers are more likely to publish results that confirm well-known thresholds (3.5%, 10%, 25%), the clustering could reflect publication bias rather than structural regularity.

---

### Visualization

1. **Histogram/density plot** of all threshold values with band boundaries marked
2. **Stripplot** showing individual findings color-coded by method type, with band boundaries
3. **GMM component plot** showing fitted Gaussian mixture with k=3 components
4. **Funnel plot** for publication bias assessment
5. **Method × domain crosstab** showing which cells contain threshold findings

---

### Output

1. CSV dataset of all coded findings
2. Statistical test results (GMM fit, permutation test p-value, method/domain independence tests)
3. Publication-ready figures
4. Summary paragraph suitable for inclusion in the paper or as a supplementary appendix

---

### What Success Looks Like

**Strong result:** 30+ independently derived threshold values from 3+ method types and 3+ domains cluster into 3 bands (GMM optimal k=3, permutation p < 0.05). Band centers are approximately 4±2%, 12±4%, and 25±5%. Findings from multiple methods and domains contribute to each band.

**Moderate result:** Clustering is apparent but k=3 is not decisively better than k=2 or k=4 by BIC/AIC. The activation and cascade bands may merge. The convergence is suggestive but not statistically decisive.

**Null result:** Threshold values are randomly distributed or cluster in a way that does not correspond to the three-band model. This would require revising the convergence claim to acknowledge that the pattern may be cherry-picked from the existing literature rather than reflecting a structural regularity.

Any of these results is valuable. A strong result strengthens the paper's core claim. A null result is honest and publishable as a negative finding that constrains the theory.

---

### Implementation Notes

**Language:** Python 3.10+
**Packages:** pandas, numpy, scipy, sklearn (GaussianMixture), matplotlib, seaborn
**Data entry:** Manual entry of coded findings into a CSV file. Claude Code compiles the initial dataset from literature search; Daniel reviews and verifies.
**Compute:** Trivial. Permutation test with 10,000 iterations on <100 data points runs in seconds.
