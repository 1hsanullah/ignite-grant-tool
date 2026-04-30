# clear_rd_input — v1 monolithic

**Latency:** 13.0s  
**Word count:** 316  
**Warning flag:** No

---

Existing first-order optimisers — specifically Adam and AdaFactor — exhibit activation divergence when gradient sparsity in sparse-attention transformer architectures exceeds approximately 85%. Under these conditions, the adaptive learning-rate mechanisms in both optimisers fail to compensate for the distributional shift in gradient statistics, and the resulting instability cannot be reliably suppressed through learning-rate scheduling alone. No published method resolves this failure mode at training scale without either relaxing the sparsity constraint or accepting unacceptable convergence degradation.

Luminary ML GmbH investigates whether a curvature-aware update rule, derived from a computationally tractable approximation of the Hessian diagonal, can suppress activation divergence by modulating per-parameter step sizes according to local loss landscape geometry. It cannot be established at the outset whether the Hessian diagonal approximation will remain numerically stable under sparse-gradient conditions, whether the per-step computational overhead introduced by the curvature estimation procedure will be offset by a commensurate reduction in steps to convergence, or whether any stability gains observed in the initial test architecture will generalise to transformer configurations with differing depth, head counts, or sparsity patterns.

To resolve these uncertainties, the team conducts a systematic series of controlled training runs in which gradient sparsity level, batch size, and approximation granularity are varied independently across pre-defined experimental conditions. Ablation studies are designed to isolate the contribution of each component of the proposed update rule, distinguishing curvature-driven stabilisation from confounding effects of regularisation or initialisation. Measurable success criteria — including divergence rate, wall-clock time to a target validation loss, and numerical stability of the Hessian approximation across sparsity thresholds — are defined in advance, and results from each experimental phase inform subsequent parameter selection before the following phase begins.

---
*CONSULTANT NOTE: This document is a first-draft aid produced by Ignite Group's drafting tool and does not constitute tax advice. A qualified consultant must review all claims for technical accuracy and FZlG eligibility before submission to the BSFZ or Finanzamt.*
