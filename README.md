# wiki-as-an-mcp

<img width="1918" height="1482" alt="image" src="https://github.com/user-attachments/assets/cf9e6f64-3bfa-4219-a2d0-fc98ce9db0e8" />
Overall Design

To our best knowledge, this is the first general purpose MCP for building and using your own personal wiki (knowledge base), following the Google proposed Open Knowledge Format and Andrew Karpahyt's LLM wiki design philosophy. This MCP is task-agnostic.

[Open Knowledge Format](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
[Andrew Karpahyt's LLM wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)


Serve a git-versioned knowledge base (an OKF wiki: a folder of markdown with YAML
frontmatter) to LLM agents over the Model Context Protocol (MCP). One small server, two
modes: **read** (an agent consults one frozen version) and **manage** (a curator edits and
snapshots new versions). The wiki is a normal git repo, so versions are commits and branches,
and editing never destroys a published version.

This `main` branch is the **general-purpose server**. For a real project built on it, see the
**`auto-insurance` branch**, an LLM-agent benchmark that serves a Tweedie/GLM insurance-modeling
wiki across a good arm and silent-defect arms.

## Why

- **Frozen reads.** Read mode pins one git commit at startup and serves it, so a consumer
  stays frozen for its whole session even while the curator keeps editing.
- **Safe edits.** Manage mode edits a working tree; `kb_snapshot` commits a new version.
  Earlier commits never change, so a published version cannot be corrupted by an edit.
- **Rules travel with the data.** The rulebook (`AGENT_RULES.md`) ships inside the server as
  the MCP `instructions` and via a `kb_rules()` tool, and the write tools enforce it.
- **Portable.** It self-locates, ships a setup script, a health `doctor` that runs on every
  start, and a portability test.

## Quick start

```bash
git clone https://github.com/taikunudel/wiki-as-an-mcp
cd wiki-as-an-mcp/knowledge-mcp

# bring an OKF knowledge repo next to the server as ../knowledge (see below),
# or point --registry at one anywhere.

./setup.sh                       # checks git + Python >= 3.10, builds the venv, localizes configs
./doctor.sh                      # health check (git, venv, knowledge repo, configs)

./start.sh --mode read --version <branch-or-commit>   # serve one frozen version to an agent
./start.sh --mode manage                              # edit a working tree, then kb_snapshot
```

Agents usually connect through one of the `knowledge-mcp/mcp.read*.json` / `mcp.manage.json`
configs rather than launching `start.sh` by hand.

## The two modes

- **read** — 5 tools (`kb_index`, `kb_list`, `kb_get`, `kb_grep`, `kb_rules`), pinned to one
  commit, content served straight from git, read-only. The write tools are not registered, so
  a read session cannot even see them.
- **manage** — all 14 tools. Checks out a branch and edits its working tree; `kb_snapshot`
  commits a new version.

The 9 manage tools add: `kb_add`, `kb_update`, `kb_remove`, `kb_new_folder`, `kb_reindex`,
`kb_validate`, `kb_versions`, `kb_snapshot`, `kb_set_current`. Full input/output examples are
in `knowledge-mcp/USER_MANUAL.md`; the rulebook is `knowledge-mcp/AGENT_RULES.md`.

## Bring your own knowledge repo

The wiki is its **own git repo**, separate from this server, so the two version independently
and neither nests inside the other. Its root is an OKF v0.1 bundle:

- folders of markdown pages, each non-reserved page carrying YAML frontmatter with a non-empty
  `type`,
- a reserved `index.md` catalog in every folder, plus a reserved `log.md`,
- editions/versions are git branches and commits (a project can keep several arms as branches).

Place it next to the server as `knowledge/`, or pass `--registry /path/to/your/knowledge`.

## Git versioning

A version is a git commit; an edition is a branch. Read resolves a ref to one commit at
startup and serves that commit, so the consumer is frozen. Manage edits the working tree and
`kb_snapshot` commits a new point; earlier commits are untouched. `kb_versions` is `git branch`
+ `git log`, `kb_set_current` is `git checkout`.

## Robustness and portability

- `setup.sh` checks prerequisites, builds the venv, and rewrites the MCP configs to wherever
  you cloned the project.
- `doctor.sh` runs before every start (and on demand): git on PATH, the venv works, the
  knowledge repo is present with its branches, the configs are valid JSON. A problem stops the
  start with a fixable message.
- `portability_test.sh` copies the project to a new path and re-runs the smoke test, catching
  any machine-specific absolute path.
- Rule of thumb: clone or move it anywhere, run `setup.sh` once, then start it. A Python venv
  cannot be moved, so `setup.sh` must be re-run after a move.

## An example project (the `auto-insurance` branch)

The `auto-insurance` branch uses this server to run an LLM-agent benchmark: it serves a
Tweedie/GLM insurance-modeling wiki across a good arm and silent-defect arms, hands a task and
a grading rubric to agents, scores their models through a sealed evaluator, and collects the
logs. It is a worked example of "a knowledge base as an MCP" inside a real experiment.
