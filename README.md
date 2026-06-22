# knowledge-mcp-design

One server that serves a versioned knowledge base (an OKF wiki) to LLM agents and lets a
manager maintain it. It backs an auto-insurance Tweedie/GLM benchmark: an agent answers a
modeling task, with or without the wiki, across three wiki arms (good, silent-defect,
stronger-defect). A run is pinned to one frozen arm so its knowledge cannot change mid-run,
and the arms must all be servable at the same time.

This README is the living design doc. It records what the system is, the problems a full
per-file audit found (2026-06-21), and the design choices that make it robust.

## The four folders

| folder | role |
|---|---|
| `knowledge/` | the data: one topic, stored as a git repo (see "Versioning with git") |
| `knowledge-mcp/` | the server: one `server.py`, two modes (`read`, `manage`) |
| `operator/` | post-run support only: the task spec, the scorer, the log/score scripts |
| `bench/` | where runs execute; kept empty so a new run cannot read an old one |

How they fit together: you launch an agent yourself (with a prompt from `operator/prompts/`),
the agent reads the knowledge through the `knowledge-mcp` server (pinned to one arm), it does
its work in a folder under `bench/`, and afterward you score and analyze it with the
`operator/` scripts. The operator never launches runs.

## Quick start

```bash
# 1. set up on this machine (checks git + Python >= 3.10, builds the venv)
knowledge-mcp/setup.sh

# 2. sanity-check the server and its portability
knowledge-mcp/.venv/bin/python knowledge-mcp/smoke_test.py     # -> ALL CHECKS PASSED
knowledge-mcp/portability_test.sh                              # -> PASS

# 3. serve one frozen wiki arm to an agent (read-only)
knowledge-mcp/start.sh --mode read --version v1               # v1 good, v2 silent-defect, v3 stronger-defect

# 4. maintain the wiki (edit a working tree, then commit a new version)
knowledge-mcp/start.sh --mode manage --version v1
```

Agents usually connect through one of the `knowledge-mcp/mcp.read.*.json` configs rather than
launching `start.sh` by hand. External requirements: git, Python >= 3.10 with `mcp`; the scorer
also needs R, CASdatasets, and Docker.

## Moving or cloning to another machine (important)

Two things do not travel with a copy of the project, so after you move or clone it, run
`knowledge-mcp/setup.sh` once:

- The Python venv cannot be moved: it has its old path baked in. `setup.sh` rebuilds it.
- The MCP config files cannot locate themselves. `setup.sh` rewrites the four `mcp.*.json`
  to point at wherever the project now sits, so they work in any folder, not just
  `$HOME/knowledge-mcp-design`.

Rule of thumb, for people and for the agent: clone or move it anywhere, run `setup.sh` once,
then start it.

## The doctor (health check on every start)

`start.sh` runs a dedicated health check, `doctor.sh`, before it launches the server, on every
start. The doctor checks four things and prints OK / BAD per line:

- git is on PATH (the wiki is a git repo),
- the Python venv works (`import mcp` succeeds),
- the knowledge git repo is present with its arms (`v1`/`v2`/`v3`),
- the four `mcp.*.json` configs are valid JSON.

If anything is BAD, the start aborts with a clear, fixable message (usually: run `setup.sh`), so a
moved-but-not-set-up copy fails loudly and early instead of misbehaving. The agent connecting to
the MCP sees the same message on stderr. The server also re-checks git and the repo at startup as
a second line of defense.

You can run the doctor on its own at any time:

```bash
knowledge-mcp/doctor.sh        # prints the report, exits 0 if healthy
```

To skip it on a start (for example, rapid restarts where you know it is healthy), set
`KMCP_SKIP_DOCTOR=1`.

## Problems the audit found

Grouped by theme. Severity in parentheses.

1. Immutability was broken (high). Manage mode pointed at `current`, which pointed at the
   frozen `v1`, so every edit wrote into a published arm. There was no working copy.
2. Paths were fragile (high). The MCP configs used `${HOME}` in a field that is not run
   through a shell, so the server never launched; prompts and the operator spec carried
   absolute machine paths (`/home/taikun`, `/Users/theo`). Moving the project breaks them.
3. The catalog rules fought the code (high). The rulebook said `index.md` lists sub-folders;
   the builder listed only files and overwrote curated catalogs; three catalog formats coexisted.
4. The operator task spec was stale (high). `plan_v5.md` and `checklist_v5.md` still
   described the old on-disk wiki delivery, used date-based names, and rejected the new ones.
5. The scorer would not start (high). The evaluator Dockerfile installed only `cplm`, but
   most of the datasets need `CASdatasets`, with no skip path.
6. Operator correctness (med). Loose completion metric, unguarded file reads, scans the
   wrong folder, stale strings, broken provenance links, port and bind mismatches.

The full issue list with status is in "Issue tracker" below.

## Versioning with git (the core decision)

We wanted an elegant way to do two things: track every change to a wiki over time, and switch
which version is served. Git is built for exactly that. Its history is the change log (every
edit is a commit with a message, a diff, and a timestamp), its branches are the versions (you
switch with a checkout), and a commit is immutable, so an older version is always recoverable
by its id. We get change-tracking, version-switching, and a freezing guarantee from one
well-understood tool, instead of a home-made folder-and-symlink scheme we would have to keep
correct ourselves.

The home-made scheme (a `versions/` folder per arm, a `current` symlink, a hand-written
`registry.yaml`, and `kb_snapshot` copying folders) had no immutability guarantee: editing
landed on a frozen arm. Git removes that whole class of bug.

Decisions:
- The knowledge is its own git repo, kept alongside this one as `knowledge/`, so the project
  and the wiki version independently and neither nests inside the other.
- The three arms are branches: `v1` (good), `v2` (silent-defect), `v3` (stronger-defect).
  `v2` and `v3` branch from `v1`, so the defect is a visible diff and the shared history is real.
- Manage mode checks out an arm and edits the working tree. `kb_snapshot` commits. The
  manager never edits a frozen point, because edits become new commits and a commit is
  immutable (content-addressed; it cannot change after the fact).
- Read mode resolves a ref to one commit at startup and serves the file content straight from
  that commit, never from the working tree. The run is frozen to that commit for the server's
  whole life, even while the manager keeps committing. Because reads come from the object
  store, all three arms can be served at once from the same repo.

Why this is stronger than before: immutability is automatic, the timeline and the
defect-as-a-diff are first class, and pinning a run to a commit is exact and reproducible.

Concurrency note: the repo working tree holds one branch at a time, so one manager edits one
arm at a time. Editing several arms at once is a later add (git worktrees), not needed now.

## One source of truth for paths

- Code locates itself: `server.py`, `start.sh`, `smoke_test.py` find their own directory and
  the sibling `knowledge/` repo, so moving the whole tree does not break them.
- Files that cannot locate themselves (MCP configs, prompts) route through one anchor: a shell
  that expands `$HOME`, never a full path repeated per file.
- Rule: no machine-specific absolute path in any code, config, prompt, or doc.

## One server, two modes

- `read`: 5 tools (`kb_index`, `kb_list`, `kb_get`, `kb_grep`, `kb_rules`), pinned to one
  commit, content served from git, read-only. This is what a benchmark run uses. The write
  tools are not registered, so a read session cannot even see them.
- `manage`: all 14 tools. Checks out one arm and edits its working tree; `kb_snapshot` commits.

The rulebook (`AGENT_RULES.md`) ships in two ways: as the server's FastMCP `instructions`
(handed to every agent on connect) and via `kb_rules()`. The manage tools gate on it: the
first manage call returns the rulebook and asks the agent to retry, so the rules land in
context before any edit runs.

## OKF and the catalog

Each commit is an OKF v0.1 bundle: every non-reserved `.md` has YAML frontmatter with a
non-empty `type`; reserved `index.md`/`log.md` carry no frontmatter; every folder has an
`index.md` catalog. One catalog format, one link style. The index builder lists sub-folders
and files, and `kb_validate` checks the whole tree.

## Storage layout

This project and the wiki are TWO git repos. The wiki is its own repo, placed next to the
server as `knowledge/` (gitignored by this project), with the OKF bundle at its root and the
arms as branches:

```
knowledge-mcp-design/          this repo: the server + the operator harness
  knowledge-mcp/  operator/  bench/  README.md  .gitignore
  knowledge/                   a SEPARATE git repo, cloned/placed here (gitignored)
    concepts/ sources/ examples/ entities/ index.md log.md overview.md
    .git/                      branches: v1 (good), v2 (silent-defect), v3 (stronger-defect)
```

The server finds `knowledge/` as its sibling by default, or you point it anywhere with
`--registry <path>`.

Tool to git mapping:

| tool | git |
|---|---|
| `kb_versions` | `git branch` + `git log` (arms and timeline) |
| `kb_snapshot(message)` | `git add -A && git commit` (a new immutable point) |
| `kb_set_current(ref)` | `git checkout ref` (switch the working/default arm) |
| read of version `vN` | resolve `vN` to a commit at startup, serve content from that commit |

## Issue tracker

From a full per-file audit (2026-06-21). Done items are fixed and, where code, tested.

Done:
- Immutability: manage edits a working tree, never a published commit (git). Tested.
- The MCP configs launch through a shell so `$HOME` expands (they never started before).
- Catalog builder lists sub-folders and preserves curated descriptions; `kb_validate` also
  checks `log.md`; the rule-7 example is relative; `kb_versions` reads git (no stale string).
- Evaluator: Dockerfile installs CASdatasets + arrow (with skip-on-failure loading); binds
  localhost by default; one canonical port (8765); the datasets README calls the files manifests.
- Operator scripts: `backfill` guards missing files and scans `bench/`; `collect-results` uses
  the strict metric (`n_completed == 10`).
- Prompts and template use a `{RUN_INDEX}` slot and portable `~` paths.
- The operator spec (`plan_v5.md`, `checklist_v5.md`) now describes MCP delivery, version
  naming (`wikiv1/v2/v3`), the real harness set, and the MCP access log as the consultation
  trail; no machine paths.
- Source pages are self-contained: the dangling raw-papers provenance pointer was dropped on
  all three arms.
- Portability: `setup.sh`, a startup git check, and `portability_test.sh`.

Open:
- swautoins: `Claims` is used as a predictor of `Payment` (target leakage). This is a
  benchmark-definition decision (see "The scorer keeps the answers sealed"), left for the owner.
- The 23 "low" audit items are not yet pulled.

## Robustness and portability

The system must run on any machine, not just where it was built. Three guards:
- Code self-locates. `server.py`, `start.sh`, `smoke_test.py` find their own directory and the
  sibling `knowledge/` repo, so moving the whole tree does not break them. Files that cannot
  self-locate (the MCP configs) launch through `/bin/sh -c` so `$HOME` expands.
- One setup step per machine. `setup.sh` checks for git and Python >= 3.10 and builds the venv
  (a venv cannot be copied between machines). The server also checks at startup that git is
  present, and fails loudly if not.
- A portability test. `portability_test.sh` copies the project to a temporary path and runs the
  smoke test there, so any re-introduced absolute path is caught immediately.

External requirements: git (the wiki is a git repo) and Python >= 3.10 with the `mcp` package.
The scorer additionally needs R, the CASdatasets package, and Docker.

## The scorer keeps the answers sealed

The evaluator (`operator/evaluator/app.R`) never hands an agent the true target. It carves out a
single global test set once and serves it WITHOUT the response column; the labels stay
server-side, and scoring is admin-only (Bearer token). An agent can only submit predictions and
get back a score, it cannot read the answers.

One open data issue lives in the dataset configs, not the API: `swautoins.yaml` lists `Claims`
(the number of claims) as a predictor of `Payment` (the total claim cost). Claims is part of the
same outcome, so this is target leakage and would inflate that dataset's score. Removing `Claims`
changes the benchmark definition, so it is left as a decision rather than a silent edit.
