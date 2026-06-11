---
title: "Generalized Linear Models (GLMs)"
type: concept
tags: [method, statmod]
sources: [smyth-jorgensen-2002-tweedie-dispersion, delong-lindholm-wuthrich-2021-tweedie]
last_updated: 2026-05-15
---

## Definition
A regression framework for response distributions in the exponential dispersion family. The mean `μ_i = E[y_i]` is linked to a linear predictor via `g(μ_i) = x_i^T β`. The variance is structured as `Var(y_i) = φ · V(μ_i)` where `V(·)` is the variance function characterizing the distribution. For Tweedie, `V(μ) = μ^p`.

## When to Use
- Baseline model for almost any pricing exercise; interpretable, fast, well-understood
- When the linear-on-link-scale assumption is plausible after standard transforms (log income, log vehicle value)
- Required by regulators in many jurisdictions for "explainable" auto/home/health rate filings

## When NOT to Use
- When nonlinear effects or interactions are substantial — use [[GeneralizedAdditiveModels]] (smooth effects) or [[GradientTreeBoosting]] (full nonlinearity)
- When the number of correlated predictors is large — regularization is essential; see [[GroupedElasticNet]]
- When random effects are needed — see [[GeneralizedLinearMixedModels]]

## Canonical Call
```R
fit <- glm(formula = CLM_AMT ~ AGE + BLUEBOOK + INCOME + AREA,
           data    = train,
           family  = tweedie(var.power = 1.5, link.power = 0))   # for Tweedie
# Or family = poisson(link="log") for frequency, Gamma(link="log") for severity

y_hat <- predict(fit, newdata = test, type = "response")
```
See `[[examples/smyth-jorgensen-2002-tweedie-dispersion]]`.

## Key Hyperparameters
| Name | Role | Default | Paper-recommended |
|---|---|---|---|
| `family` | distribution + link | gaussian | `tweedie(var.power, link.power=0)` for total claim; `poisson` / `Gamma` for split |
| `weights` | observation weights | 1 | exposure (for Poisson) or claim count (for severity) |
| `offset` | known shift on link scale | 0 | `log(exposure)` for Poisson frequency |
| `na.action` | NA handling | `na.omit` | be deliberate — `na.exclude` preserves row alignment for predict |

## Common Pitfalls
- **`predict.glm(..., type = "link")` vs `"response"`** — link returns the linear predictor, response returns the mean. For pricing, you almost always want `"response"`.
- **Unseen factor levels in test data** — `glm` silently produces NA or errors. Always pre-process factors to align levels: `test$AREA <- factor(test$AREA, levels = levels(train$AREA))`.
- **Hardcoded `var.power`** — for Tweedie family, profiling matters (see [[TweedieVariancePowerEstimation]])
- **Aliased coefficients from collinear predictors** — `glm` silently drops; check `summary(fit)$aliased`
- **No regularization** — when p > n/10, the GLM overfits; use [[GroupedElasticNet]] or shrinkage in [[GeneralizedAdditiveModels]] with `select = TRUE`

## Sources
- [[smyth-jorgensen-2002-tweedie-dispersion]] — uses GLM as base
- [[delong-lindholm-wuthrich-2021-tweedie]] — Poisson and gamma GLMs as the standard alternative
