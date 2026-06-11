# Operator guide — running the benchmark

This is the guide for the **session manager** — a human operator or a master operator
agent — who sets up the machine, starts the eval API, launches benchmark agents, and
evaluates results. (Project overview and findings live in [`README.md`](README.md);
this file is purely "how to run it".)

This repo runs a benchmark where an **AI coding agent** is dropped into a workspace and
asked to autonomously write R that fits four Tweedie-family models (`tweedie_gam`,
`grplasso`, `grpnet`, `tdboost`) across **six held-out insurance datasets**, scoring
each by **Gini** against a sealed eval API. The agent may read a local knowledge wiki
(`knowledge-base/`) but must discover dataset-specific fixes itself — the wiki omits
them by design. The benchmark measures whether the agent + wiki **transfer to data
they have not seen**.

Read this top to bottom and you — a human **or** an operator agent — can go from a
fresh clone to a running benchmark.

## The two roles
- **Operator** (you, or a master operator agent): sets up the machine, starts the eval
  API, launches the benchmark agents, resumes them when they stall, evaluates results.
  Your guides are this file, **`MASTER.md`** (the operator-agent playbook),
  **`RUNBOOK.md`** (per-harness launch commands), and `setup.sh`.
- **Benchmark agent**: the model under test. It runs in a **materialized workspace**
  (built by `operator/make-workspace.sh`) and reads only what's there: its arm's
  contracts (`CLAUDE.md`/`AGENTS.md`/`GEMINI.md`), `knowledge-base/` (if the arm has
  one), and the spec. `do_not_read/`, `FINDINGS.md`, other arms' wikis — physically
  absent from its world. You don't write its code — you launch it and it does the work.

## What's in here
| path | what |
|---|---|
| `CLAUDE.md` · `AGENTS.md` · `GEMINI.md` | the benchmark agent's contract (one per harness family) |
| `plan_v5.md` · `checklist_v5.md` | the task spec the agent implements |
| `MASTER.md` | the master operator agent's playbook: start → monitor → resume → evaluate |
| `conditions/` | the experimental arms (`wiki-0531/`, `wiki-0530/`, `no-wiki/`): agent contracts + wiki payload each |
| `evaluator/` | the sealed scoring API: `app.R` (plumber), `Dockerfile`, 6 dataset manifests |
| `operator/` | run tooling: auto-resume loops, results aggregator, eval-API watchdog (paths self-locate) |
| `setup.sh` · `smoke.sh` · `.env.example` | environment bootstrap, end-to-end check, config |
| `RUNBOOK.md` · `roster.yaml` · `task_prompt.template.txt` | per-harness launch commands, the model grid, the prompt template |

## Getting started — four steps

### 0. Prerequisites
- **R ≥ 4.x** with a C/Fortran toolchain (some packages compile from source).
- `curl` and `python3` (the operator loops use them).
- One or more **agent harness CLIs**, each with its own account / API key — see
  `RUNBOOK.md`: `claude` (Claude Code), `codex` (OpenAI Codex), `agy` (Antigravity),
  `openclaw`. These are the one piece that can't be scripted — they're your paid logins.

### 1. Install the environment
```bash
./setup.sh
```
Installs the R packages — the CRAN ones (`mgcv`, `HDtweedie`, `TDboost`, `tweedie`,
`statmod`, `dglm`, `cplm`, `plumber`, `jsonlite`, `yaml`) **and `CASdatasets`, which is
not on CRAN** (it feeds 5 of the 6 datasets, so it's pulled from its own repo). Then it
verifies every dataset loads. Want bit-for-bit reproducibility instead? Build the API
from `evaluator/Dockerfile`.

> **Why a script is needed at all:** the datasets aren't stored in this repo — they
> ship *inside* those R packages, so "get the data" = "install the packages." A plain
> `install.packages(...)` won't find `CASdatasets`; `setup.sh` knows where it lives.

### 2. Configure
```bash
cp .env.example .env       # then edit: the eval-API token + your harness API key(s)
```

### 3. Start the eval API and verify end-to-end
```bash
./setup.sh --start-api     # starts the scoring API on :8765
./smoke.sh                 # fits a trivial model on one dataset and scores it
```
`smoke.sh` prints a Gini value if the whole pipeline — data → fit → submit → score —
works. Green here means the box is ready.

### 4. Materialize the arm's clean-room workspace
Agents never run inside the repo. Pick the condition and build its workspace:
```bash
operator/make-workspace.sh wiki-0531        # or wiki-0530 / no-wiki / exp-*
operator/check-structure.sh ~/bench/ws-wiki-0531   # must print PASS
```
The workspace contains only that arm's contracts + wiki (if any) + the spec +
`CONDITION.txt` (condition, repo SHA, wiki version — recorded provenance). Other
arms' wikis, `conditions/`, `do_not_read/`, and analysis docs physically don't
exist there — that's the knowledge separation.

### 5. Launch a benchmark run
Follow **`RUNBOOK.md`** for the exact per-harness command, **with cwd = the
workspace**. In short: export the run env (`WIKI_VERSION` derived from
`CONDITION.txt`), hand the agent the prompt from `task_prompt.template.txt`, and let
it run (2–4 h typical). A run is **complete when its `results/summary.csv` has all
24 cells (6 datasets × 4 models) populated with a non-NA `mean_eval_gini`.**

## Notes
- **Secrets:** `evaluator/secrets/secrets.rds` is gitignored. The API runs without it
  (per-trial splits reseed randomly); provide it only to reproduce the *exact* original
  splits.
- **`do_not_read/`** holds operator analysis + results. It's off-limits to the
  *benchmark agent* (to prevent leakage), not to you as operator.
- **`FINDINGS.md` / `README.md`** contain the analysis of completed runs — including
  the dataset-specific fixes the benchmark deliberately withholds. Same rule: off-limits
  to benchmark agents, fine for you.
