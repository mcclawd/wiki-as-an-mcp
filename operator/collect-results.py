#!/usr/bin/env python3
"""
Aggregate benchmark results across run-* folders.

Default: one completeness line per run (done/20). A cell counts as done only when its
results/summary.csv row has a real mean_eval_gini AND n_completed == 10 (all 10 draws).
This is the STRICT rule: a non-NA mean alone is not enough.
--tidy : dump a tidy CSV (run,dataset,model,mean_eval_gini,mean_test_gini,success_rate)
         for every run to stdout, for pivoting/comparison.

Usage:
  python3 operator/collect-results.py [--tidy] [--root DIR ...]
  --root DIR : scan run-* under DIR(s) instead of the repo root — pass each
               clean-room workspace, e.g. --root ~/knowledge-mcp-design/bench/ws-wiki-0531 ~/knowledge-mcp-design/bench/ws-no-wiki
               (globs expanded by your shell work too: --root ~/knowledge-mcp-design/bench/ws-*)
"""
import csv, glob, os, sys

WS = os.environ.get("WORKSPACE") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = 20  # 5 datasets x 4 models
V5_MODELS = {"tweedie_gam", "grplasso", "grpnet", "tdboost"}  # GLM dropped in v5


def roots_from_argv():
    if "--root" not in sys.argv:
        return [WS]
    i = sys.argv.index("--root")
    roots = []
    for a in sys.argv[i + 1:]:
        if a.startswith("--"):
            break
        roots.append(os.path.expanduser(a))
    return roots or [WS]


def rows_for(run_dir):
    path = os.path.join(run_dir, "results", "summary.csv")
    if not os.path.exists(path):
        return None
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def is_complete(row):
    """STRICT completion: a real mean_eval_gini AND all 10 draws done (n_completed == 10)."""
    g = (row.get("mean_eval_gini") or "").strip().strip('"')
    if g in ("", "NA", "NaN"):
        return False
    n = (row.get("n_completed") or "").strip().strip('"')
    try:
        return int(float(n)) == 10
    except ValueError:
        return False


def main():
    tidy = "--tidy" in sys.argv
    roots = roots_from_argv()
    runs = sorted(r for root in roots for r in glob.glob(os.path.join(root, "run-*")))
    if not runs:
        print(f"no run-* folders under: {', '.join(roots)}", file=sys.stderr)
        sys.exit(1)

    if tidy:
        w = csv.writer(sys.stdout)
        w.writerow(["run", "dataset", "model", "mean_eval_gini", "mean_test_gini", "success_rate"])
        for d in runs:
            rows = rows_for(d)
            if not rows:
                continue
            for r in rows:
                w.writerow([os.path.basename(d), r.get("dataset"), r.get("model"),
                            r.get("mean_eval_gini"), r.get("mean_test_gini"), r.get("success_rate")])
        return

    print(f"{'run':<70} {'done':>9} status")
    warned = False
    for d in runs:
        rows = rows_for(d)
        name = os.path.basename(d)
        if rows is None:
            print(f"{name:<70} {'-':>9} no summary.csv yet")
            continue
        if rows and not warned and "n_completed" not in rows[0]:
            print("[warn] summary.csv has no n_completed column; strict completion cannot be verified",
                  file=sys.stderr)
            warned = True
        done = sum(1 for r in rows if r.get("model") in V5_MODELS and is_complete(r))
        status = "COMPLETE" if done >= TARGET else f"incomplete ({TARGET - done} to go)"
        print(f"{name:<70} {done:>6}/{TARGET} {status}")


if __name__ == "__main__":
    main()
