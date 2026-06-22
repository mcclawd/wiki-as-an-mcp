# prompts

Ready-to-paste prompts, one per agent we have benchmarked, filled from
`../task_prompt.template.txt`. Each file has a commented header (the launch command +
the MCP-version reminder) and the paste-able prompt below the divider.

## Use
1. Pick the file for your model (e.g. `opus47.txt`).
2. Choose the wiki version for this run: v1 / v2 / v3, or v0 for the no-wiki control.
   - v1/v2/v3: start the read server pinned to that version (header shows the command) so
     the agent's kb_* tools serve that arm.
   - v0: do not start the MCP; the agent gets no knowledge tools.
3. The files default to WIKI_VERSION=v1, RUN_INDEX=1. For another arm, change `wikiv1`
   and `run1` in the folder-name line (and the `--version` in the MCP command) to match.
4. Run the launch command at the top, then paste the prompt (everything below the divider).

Note: antigravity model names contain spaces/parentheses, so the folder-name slot uses the
short label (e.g. `gemini31pro`) while the `You are` line uses the real model name.
