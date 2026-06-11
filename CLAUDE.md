# Workspace Instructions for Claude Code — OPERATOR territory

This repo is the **operator side** of the auto-insurance LLM-agent benchmark.
Benchmark agents do **not** run here anymore — they run in **materialized clean-room
workspaces** that contain only their condition's payload. If you are reading this
file, you are an operator/analysis session, not a benchmark agent.

(`AGENTS.md` and `GEMINI.md` mirror this file for other harnesses.)

---

## 🧪 Experimental Design — Read This Before Analyzing Anything

This project is a **generalization benchmark**. The wiki conditions under
`conditions/wiki-*/` were built from a **reserved corpus**; the benchmark datasets
served by the eval API (`fremtpl2`, `ausprivauto`, `auto_insurance`, `bemtpl97`,
`sgautonb`, `swautoins`) are **deliberately held out** from the wiki — agents see
them for the first time during a run.

- **`gaps.md` (inside each wiki) is a leakage quarantine, not a backlog.** Failure
  modes discovered on held-out benchmark data must NOT be promoted into concept
  pages of an arm that is still being measured. (The 0530→0531 update did promote
  them — deliberately, as a separate experimental arm.)
- Dataset-specific fixes (e.g. "fremtpl2 GLM needs `mustart`") are *outside* the
  wiki's scope by design; agents are expected to discover them from R warnings and
  debugging, not lookup.
- "Agents who read the wiki more performed worse" should be read as "the wiki
  correctly omits dataset-specific fixes," not "the wiki is misleading."

---

## Repo layout (conditions-as-data, clean-room execution)

```
conditions/             ← the experimental payloads, side by side
  wiki-0531/            ← agent contracts + knowledge-base (0531 wiki)
  wiki-0530/            ← agent contracts + knowledge-base (0530 wiki)
  no-wiki/              ← agent contracts only (control arm)
operator/
  make-workspace.sh     ← materialize core + ONE condition into an agent workspace
  check-structure.sh    ← verify a workspace matches its CONDITION.txt stamp
plan_v5.md, checklist_v5.md   ← the task spec (invariant across all conditions)
evaluator/              ← sealed scoring API
do_not_read/            ← the user's permanent analysis vault — never relocate it
paper/                  ← analysis workspace (gitignored)
FINDINGS.md, OPERATOR.md, MASTER.md, RUNBOOK.md, roster.yaml  ← operator docs
```

**Launch flow:** `operator/make-workspace.sh <condition>` →
`operator/check-structure.sh <ws>` (must PASS) → launch the benchmark agent with
cwd = the workspace. The workspace physically contains only: that condition's
contracts, its knowledge-base (if any), the spec, and `CONDITION.txt` (condition
name + repo SHA + wiki version — a recorded fact, not a folder-name label).
Knowledge separation is **by construction**: other wiki versions, `conditions/`,
`do_not_read/`, `paper/`, and `FINDINGS.md` do not exist in the agent's world.

**Rules for operator sessions here:**
- Never copy analysis, findings, or other conditions into an agent workspace.
- Never edit `conditions/wiki-0530/` or `conditions/wiki-0531/` content — they are
  frozen experimental arms. New wiki experiments = new `conditions/exp-*/` folders.
- The `no-wiki` **branch** is legacy (an experiment may still be running against
  it remotely) — do not modify or delete it; its payload now lives in
  `conditions/no-wiki/`.
- Spec changes (`plan_v5.md` etc.) invalidate cross-arm comparability — do not
  edit the spec while any arm's data collection is incomplete.

## Workspace Conventions

- The `do_not_read/` folder is the user's analysis vault: out of scope for
  benchmark agents (and absent from their workspaces), normal territory for you.
- `README.md`, `FINDINGS.md`, `OPERATOR.md` are human/operator documents about
  completed runs.
