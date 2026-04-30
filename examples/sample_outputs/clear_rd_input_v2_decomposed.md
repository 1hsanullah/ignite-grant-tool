# clear_rd_input — v2 decomposed

**Latency:** 18.1s  
**Word count:** 336  
**Warning flag:** No

---

### Stage 1 — Failure mode

First-order optimisers — specifically Adam and AdaFactor — fail under sparse-attention training regimes when gradient sparsity exceeds approximately 85%. In this regime, the adaptive moment estimates that these optimisers maintain become unreliable: sparse gradient signals cause the second-moment accumulator to underestimate true curvature in active parameter directions, producing step sizes that are systematically miscalibrated. The resulting activation divergence destabilises training in a manner that learning-rate scheduling alone cannot correct, because scheduling operates on a global scalar and cannot resolve the parameter-local miscalibration that sparse gradients introduce. No published optimisation method has demonstrated reliable suppression of this divergence while remaining computationally tractable at scale.

### Stage 2 — Unknowns at outset

At the project's outset, the research team cannot establish whether a Hessian diagonal approximation remains numerically stable when gradient sparsity exceeds 85%, nor whether the approximation's fidelity degrades non-linearly at higher sparsity thresholds. It is unknown whether the curvature-aware update rule will suppress activation divergence sufficiently to permit stable convergence, or whether residual miscalibration will persist in parameter subsets with near-zero gradient mass. The per-step compute overhead of the approximation procedure is unquantified, and it cannot be determined in advance whether convergence acceleration will offset this cost at scale. Whether the update rule generalises across transformer architectures beyond the initial test configuration also remains unresolved before experimentation begins.

### Stage 3 — Synthesis

Luminary ML GmbH investigates whether a curvature-aware second-order optimisation algorithm can suppress activation divergence in sparse-attention transformer models trained at gradient sparsity levels exceeding 85% — a failure regime in which established first-order optimisers cannot maintain stable training. Under these conditions, the adaptive moment estimates maintained by Adam and AdaFactor become systematically unreliable: sparse gradient signals cause the second-moment accumulator to underestimate true curvature in active parameter directions, producing per-parameter step sizes that are miscalibrated in a manner that global learning-rate scheduling cannot correct. No published optimisation method has demonstrated reliable mitigation of this divergence while remaining computationally tractable at scale.

The project's central hypothesis is that a curvature-aware update rule — derived from a computationally tractable approximation of the Hessian diagonal — can modulate step sizes according to local loss-landscape geometry and thereby suppress this divergence. It cannot be established at the project's outset whether the Hessian diagonal approximation remains numerically stable when gradient sparsity exceeds 85%, nor whether the approximation's fidelity degrades non-linearly at higher sparsity thresholds. It is further unknown whether residual miscalibration will persist in parameter subsets carrying near-zero gradient mass, whether the per-step compute overhead of the approximation will be offset by accelerated convergence at scale, and whether any demonstrated stability generalises across transformer architectures beyond the initial test configuration.

To resolve these unknowns, the team will conduct a systematic series of controlled training runs, varying sparsity levels, batch sizes, and approximation granularity across defined experimental conditions. Ablations are designed to isolate the contribution of individual components of the update rule, with quantitative success criteria defined in advance for numerical stability, convergence rate, and per-step computational overhead. Results at each stage will be evaluated against those criteria to determine whether the methodology requires revision before proceeding.

---
*CONSULTANT NOTE: This output is a drafting aid produced by an automated system and does not constitute tax or legal advice. A qualified consultant must review this statement for technical accuracy, completeness, and compliance with current BSFZ submission requirements before any application is filed.*
