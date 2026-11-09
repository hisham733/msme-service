# 16 — Skill `grill-me` installed

## 1. What was installed

`mattpocock/skills` → **`grill-me`** (plus its dependency **`grilling`**, because
`grill-me/SKILL.md` only says *"Call the Skill tool with `grilling`"*).

| skill | path | mode |
|---|---|---|
| `grill-me` | `.agents/skills/grill-me` | copy |
| `grilling` | `.agents/skills/grilling` | copy |

Both are project-scoped, security-assessed safe (Gen safe · Socket 0 alerts · Snyk low).

Because opencode v1 discovers skills from `.opencode/skills` (and `.claude/skills`), not
`.agents/skills`, two relative symlinks were added:

- `.opencode/skills/grill-me → ../../.agents/skills/grill-me`
- `.opencode/skills/grilling → ../../.agents/skills/grilling`

✅ nothing to decide.

## 2. Node version

The CLI refused to run on the default Node **v20.19.6** (`fs/promises` has no `glob`; engine
requires ≥ 22.20.0). It was run with the already-installed nvm **v22.16.0** — no system
change, no install. If you want `npx skills` to work in a plain shell, Node 22+ must be the
default (`nvm alias default 22.16.0`).

⭐ Decision — §2: make Node 22 the default, or keep prefixing the PATH each time?
Recommendation: make it default (one-time, reversible, no runtime impact on the Python service).

## 3. Use

Reload the session (skills are read at startup), then the skill list should show
`grill-me`. Asking "grill me on X" triggers `grilling`: it maps the design as a tree and
asks the whole current frontier in numbered rounds with a recommended answer per question.

✅ nothing to decide.

## Recap

| item | state |
|---|---|
| `grill-me` | installed (project) |
| `grilling` (dependency) | installed (project) |
| opencode discovery | symlinked into `.opencode/skills` |
| Node | ran on nvm v22.16.0 |
| tests / app | untouched — install only |

## What I recommend next

Start a **new session** (skills load at startup) with: *"grill me on the N-3 report-link plan"* —
medium thinking effort, because the grilling round is mostly judgement, not measurement.
