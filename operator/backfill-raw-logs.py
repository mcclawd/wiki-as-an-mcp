#!/usr/bin/env python3
"""backfill-raw-logs.py — copy each run's RAW harness session jsonl into its folder.

Many benchmark agents (esp. openclaw zai/* and codex) never write the
logs/session_snapshot.jsonl the workspace CLAUDE.md asks for, so their raw
trajectory lives only in the harness session store. Later behavioral analysis
needs it co-located with the run. This script backfills it as COPIES (originals
left in the store), into <run>/logs/harness_sessions/<key-or-rollout>.jsonl plus
a MANIFEST.txt.

Mapping is authoritative + verified:
  openclaw -> session key (recorded in runs.log) resolved via sessions.json to a
              sessionId UUID; only keys whose run-TAG matches the folder's tag are
              taken (an incidental `ls` of another run's folder mentions it a few
              times; the real driver mentions it 100s of times — printed as a check).
  codex    -> the rollout under ~/.codex/sessions/** that mentions the folder name
              the most (the driver), not the incidental ls-ers.

Idempotent: folders that already have an in-folder session_snapshot.jsonl OR a
populated harness_sessions/ are skipped unless --force. Re-run safely after late
resumes to capture newly-created sessions. Quarantined + dropped (lane E) folders
are skipped.

Usage: python3 operator/backfill-raw-logs.py [--force] [run-folder ...]
"""
import json, os, glob, shutil, sys, subprocess

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = os.path.join(WS, "bench")               # runs live here, not at the repo root
SESS = os.path.expanduser("~/.openclaw/agents/main/sessions")
CODEX = os.path.expanduser("~/.codex/sessions")
RUNS_LOG = os.path.join(WS, "runs.log")
FORCE = "--force" in sys.argv
targets = [a for a in sys.argv[1:] if not a.startswith("--")]
# scan bench/ for run folders; fall back to the repo root only if bench/ is absent
os.chdir(BENCH if os.path.isdir(BENCH) else WS)

def tag(key): return key.replace("agent:main:", "").split("-wiki0")[0]
def mentions(path, needle):
    try: return open(path, errors="ignore").read().count(needle)
    except OSError: return 0
def has_log(d):
    return bool(glob.glob(f"{d}/logs/**/session_snapshot*.jsonl", recursive=True) or
                glob.glob(f"{d}/logs/harness_sessions/*.jsonl"))

# ---- openclaw key map (guarded: these come from the launch store; absent in a fresh tree) ----
_sj_path = f"{SESS}/sessions.json"
sj = json.load(open(_sj_path)) if os.path.exists(_sj_path) else {}
key2sid = {k: v.get("sessionId") for k, v in sj.items() if isinstance(v, dict) and v.get("sessionId")}
tag2folder, folder_keys, ped = {}, {}, []
_runs = open(RUNS_LOG, errors="ignore") if os.path.exists(RUNS_LOG) else []
if not _runs:
    print(f"[warn] no runs.log at {RUNS_LOG}; openclaw key mapping skipped (codex backfill still works)",
          file=sys.stderr)
for line in _runs:
    p = [x.strip() for x in line.split("|")]
    if len(p) < 4 or not p[3].startswith("agent:main:"): continue
    folder, key = p[2], p[3]
    if folder.startswith("run-openclaw") and "<" not in folder:
        folder_keys.setdefault(folder, set()).add(key); tag2folder.setdefault(tag(key), folder)
    else: ped.append(key)
for key in ped + list(key2sid):
    f = tag2folder.get(tag(key))
    if f: folder_keys.setdefault(f, set()).add(key)

def backfill_openclaw(f):
    dest = f"{f}/logs/harness_sessions"; os.makedirs(dest, exist_ok=True)
    rows = []
    for k in sorted(folder_keys.get(f, [])):
        sid = key2sid.get(k); src = f"{SESS}/{sid}.jsonl" if sid else None
        if not src or not os.path.exists(src): continue
        safe = k.replace("agent:main:", "").replace(":", "_")
        shutil.copy2(src, f"{dest}/{safe}.jsonl")
        tj = f"{SESS}/{sid}.trajectory.jsonl"
        if os.path.exists(tj): shutil.copy2(tj, f"{dest}/{safe}.trajectory.jsonl")
        rows.append((k, sid, mentions(src, os.path.basename(f))))
    if rows:
        with open(f"{dest}/MANIFEST.txt", "w") as m:
            m.write(f"Raw openclaw session logs (copies; originals in {SESS}).\n")
            for k, sid, c in rows: m.write(f"  {k}  ->  {sid}  (folder-mentions={c})\n")
    return len(rows)

def backfill_codex(f):
    dest = f"{f}/logs/harness_sessions"
    best, bestc = None, 0
    try:
        cand = subprocess.run(["grep", "-rl", os.path.basename(f), CODEX],
                              capture_output=True, text=True).stdout.split()
    except Exception: cand = []
    for r in cand:
        c = mentions(r, os.path.basename(f))
        if c > bestc: best, bestc = r, c
    if not best or bestc < 20: return 0
    os.makedirs(dest, exist_ok=True)
    shutil.copy2(best, f"{dest}/{os.path.basename(best)}")
    with open(f"{dest}/MANIFEST.txt", "w") as m:
        m.write(f"Raw codex rollout (copy; original in {CODEX}).\n  {best}  (folder-mentions={bestc})\n")
    return 1

all_folders = targets or sorted(glob.glob("run-*/"))
done = []
for f in all_folders:
    f = f.rstrip("/")
    if not os.path.isdir(f) or os.path.exists(f + "/QUARANTINED.txt"): continue
    if os.path.basename(f).startswith("run-openclaw-or-"): continue   # lane E dropped
    if has_log(f) and not FORCE: continue
    n = backfill_openclaw(f) if f.startswith("run-openclaw") else (
        backfill_codex(f) if f.startswith("run-codex") else 0)
    if n: done.append((f, n))
for f, n in done: print(f"  backfilled {n} session(s)  {f}")
print(f"TOTAL: {len(done)} folder(s)")
