# Workspace Instructions (Codex / OpenCode / OpenClaw) — OPERATOR territory

This repo is the **operator side** of the auto-insurance benchmark. Benchmark
agents do NOT run here — they run in materialized clean-room workspaces built by
`operator/make-workspace.sh <condition>` (payloads live under `conditions/`).

If you are an agent reading this at the repo root, you are an **operator**:
read `MASTER.md` (playbook), `RUNBOOK.md` (launch commands), `OPERATOR.md`
(setup). The benchmark agent contracts live in `conditions/<arm>/` and are
copied into each workspace — they are not instructions for you.

Rules: never copy `conditions/`, `do_not_read/`, `paper/`, or `FINDINGS.md`
into an agent workspace; never edit frozen arms (`conditions/wiki-0530|0531`);
do not touch the legacy `no-wiki` git branch (a remote experiment may still use
it); run `operator/check-structure.sh <ws>` before every launch.

Full details: [CLAUDE.md](CLAUDE.md) (same content, Claude Code mirror).
