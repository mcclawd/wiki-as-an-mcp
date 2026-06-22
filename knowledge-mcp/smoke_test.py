#!/usr/bin/env python3
"""Standalone MCP client that drives the git-backed knowledge-mcp server in both modes.

Self-locating. Read mode serves a frozen commit (v1). Manage runs on a THROWAWAY branch
(_smoketest, branched from v1), so the published arms v1/v2/v3 are never touched. The test
records the v1/v2/v3 commit ids before and after and asserts they are unchanged.
"""
import asyncio
import subprocess
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent            # the knowledge-mcp/ folder
REG = str(HERE.parent / "knowledge")              # sibling knowledge repo (flat: it IS the bundle repo)
TOPIC = "knowledge"
REPO = Path(REG)
WORK = "_smoketest"        # throwaway branch the write/version tests use
PY = sys.executable

READ_TOOLS = {"kb_index", "kb_list", "kb_get", "kb_grep", "kb_rules"}
MANAGE_TOOLS = READ_TOOLS | {"kb_add", "kb_update", "kb_remove", "kb_new_folder",
                             "kb_reindex", "kb_validate", "kb_versions",
                             "kb_snapshot", "kb_set_current"}


def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)


def sha(ref):
    return git("rev-parse", ref).stdout.strip()


def params(mode, version=None):
    args = [str(HERE / "server.py"), "--mode", mode, "--registry", REG,
            "--topic", TOPIC, "--log-dir", "/tmp/kb-smoke"]
    if version:
        args += ["--version", version]
    return StdioServerParameters(command=PY, args=args)


async def text(session, name, args=None):
    r = await session.call_tool(name, args or {})
    return r.content[0].text


async def read_checks():
    async with stdio_client(params("read")) as (r, w):       # default branch = v1
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = {t.name for t in (await s.list_tools()).tools}
            assert tools == READ_TOOLS, f"read tools wrong: {sorted(tools)}"
            print(f"read mode: exactly {len(tools)} tools, no write tools  OK")

            got = await text(s, "kb_get", {"page_id": "concepts/TweedieDistribution.md"})
            truth = (REPO / "concepts/TweedieDistribution.md").read_text()
            assert got == truth, "byte-parity FAILED (git-served != working file)"
            print(f"kb_get byte-parity (served from commit): {len(got)} chars match  OK")

            idx = await text(s, "kb_index", {"folder": "concepts"})
            assert idx.lstrip().startswith("#"), "kb_index not a catalog"
            print(f"kb_index('concepts'): {idx.splitlines()[0]!r}  OK")

            grep = await text(s, "kb_grep", {"query": "tweedie"})
            assert "match(es)" in grep, "kb_grep no matches"
            print(f"kb_grep('tweedie'): {grep.splitlines()[0]}  OK")

            rules = await text(s, "kb_rules")
            assert "Knowledge Manager" in rules, "kb_rules wrong"
            print("kb_rules() returns the rulebook  OK")

            trav = await text(s, "kb_get", {"page_id": "../../../etc/passwd"})
            assert trav.startswith("ERROR"), "traversal guard FAILED"
            print("traversal guard blocks ../../../etc/passwd  OK")


async def manage_checks():
    async with stdio_client(params("manage", WORK)) as (r, w):   # edits the throwaway branch
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = {t.name for t in (await s.list_tools()).tools}
            assert tools == MANAGE_TOOLS, f"manage tools wrong: {sorted(tools)}"
            print(f"manage mode: exactly {len(tools)} tools  OK")

            first = await text(s, "kb_validate")
            assert first.startswith("STOP: read the knowledge rules"), "rules gate did not fire"
            print("rules gate: first manage call returns the rulebook  OK")

            v = await text(s, "kb_validate")
            assert v.startswith("OKF v0.1: PASS"), f"validate not pass: {v[:80]}"
            print(f"kb_validate after gate: {v.splitlines()[0]}  OK")

            add = await text(s, "kb_add", {"page_id": "concepts/_SmokeTest.md",
                                           "type": "concept", "title": "Smoke Test",
                                           "description": "temporary test page."})
            assert add.startswith("added concepts/_SmokeTest.md"), add
            assert "validate: PASS" in add, add
            print("kb_add: created page in working tree, rebuilt index, validate PASS  OK")

            back = await text(s, "kb_get", {"page_id": "concepts/_SmokeTest.md"})
            assert "type: concept" in back and "Smoke Test" in back, back
            print("kb_get sees the uncommitted new page  OK")

            rm = await text(s, "kb_remove", {"page_id": "concepts/_SmokeTest.md"})
            assert rm.startswith("removed"), rm
            print("kb_remove: deleted page, rebuilt index  OK")

            snap = await text(s, "kb_snapshot", {"message": "smoke: round-trip"})
            assert snap.startswith("committed on _smoketest"), snap
            print(f"kb_snapshot: {snap.splitlines()[0]}  OK")

            vers = await text(s, "kb_versions")
            assert WORK in vers and "v1" in vers, vers
            print("kb_versions lists the arms incl the throwaway branch  OK")

            sc = await text(s, "kb_set_current", {"ref": "v1"})
            assert "_smoketest -> v1" in sc, sc
            await text(s, "kb_set_current", {"ref": WORK})  # switch back so cleanup is simple
            print("kb_set_current: switched arms and back  OK")


def setup():
    git("checkout", "-q", "v1")
    git("branch", "-D", WORK)              # ignore error if absent
    git("branch", WORK, "v1")             # fresh throwaway branch from v1


def cleanup():
    git("checkout", "-q", "v1")
    git("branch", "-D", WORK)


async def main():
    setup()
    before = {b: sha(b) for b in ("v1", "v2", "v3")}
    await read_checks()
    print()
    await manage_checks()
    cleanup()
    after = {b: sha(b) for b in ("v1", "v2", "v3")}
    assert before == after, f"IMMUTABILITY FAILED: {before} -> {after}"
    print(f"\nimmutability: v1/v2/v3 commit ids unchanged by managing  OK\n  {after}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        cleanup()
    print("\nALL CHECKS PASSED")
