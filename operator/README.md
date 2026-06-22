# operator — post-run support (no autonomous launching)

You launch agents yourself by prompting them with the template, and point them at the knowledge MCP. This folder holds only what you run by hand, before and after a run.

What you hand the agent:
- `plan_v5.md`, `checklist_v5.md` the task and the checklist it is graded on
- `task_prompt.template.txt` the prompt skeleton you fill in and paste

How a run gets scored:
- `evaluator/` the sealed scorer (an R service plus held-out test data)
- `eval-api-watchdog.sh` keeps the scorer alive

Your post-run jobs:
- `backfill-raw-logs.py` job 1: copy a run's raw log into its run folder
- `collect-results.py` job 2: combine every run's result CSV into one table
- `analyze/` job 3: your raw-log analysis scripts


Position in the project: the operator side. It does not launch or babysit runs; it gives you the task to hand out, the way to score a finished run, and the scripts to gather logs and results.
