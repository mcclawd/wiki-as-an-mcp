# datasets

Dataset manifests: one YAML per dataset that tells the scorer how to build each held-out
test set (the source, the response column, the predictors, the split ratios). The actual
data is loaded from these sources at scorer startup, it is not stored here.

The response column is never handed to an agent: the scorer carves out a single sealed test
set and serves it without labels, so an agent cannot read the answers (see `app.R`).

Position in the project: the configs behind the `evaluator/` scorer. Do not copy these into
any knowledge version or into any agent's workspace.
