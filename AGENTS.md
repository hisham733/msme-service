# AGENTS.md — msme-service (opencode)

A session opened here works on the AI_News web service (receive · filter · repurpose). Live data,
credentials and the 2.8 GB email archives are off-limits to destructive edits.

- Read `README.md` first (the project map + hard rules), then `NOW.md`.
- Always-loaded rules: `NOW.md` + `.claude/rules/msme-service.md` (declared in `opencode.json`).
- Global rules come from `~/.claude/CLAUDE.md` + the opencode adapter
  (`~/.config/opencode/instructions/opencode-rules.md`).
- Reply per turn: `session-analysis/<YYYY-MM-DD>_S<nn>_<subject>/<n>_<subject>.md`; chat = summary only.
- **`S<nn>` = the project's working-day number — one folder per calendar day.** Extra sessions the same
  day add files `2_…`, `3_…` inside that day's folder; a new folder only after midnight.
- Verify claims by running the app or test, not by re-reading docs: `python3 -m compileall -q *.py`,
  then `curl -s localhost:8898/health` / `localhost:8900/health` when the stack is up.
- This folder gets its **own memory container** — always open sessions in this folder.
