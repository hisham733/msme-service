# 4 — status icons in the todo file names and index

**Deliverable:** every todo file is now named `<status icon> T-xxx.md` (e.g. `🟢 T-050.md`), its
heading carries the same icon, and the index links to the new name. No app code changed.

## 1. What changed

`tools/build_register_indexes.py` (the generator) now:

- maps status → icon:

| Status | Icon |
|---|---|
| `open` | 🟢 |
| `in-progress` | 🚧 |
| `awaiting-user` / `awaiting-MG` | ⏳ |
| `parked` | ⏸️ |
| `closed` | ✅ |
| `decided-unbuilt` | 🔨 |
| `superseded` | 🗑️ |
| `blocked` | ⛔ |
| unknown | • |

- **renames the file** `T-050.md` → `🟢 T-050.md` (and re-renames when the status changes);
- puts the same icon on the first `## ` heading: `## 🟢 T-050 …`;
- renders the index link as `[🟢 T-050.md](🟢 T-050.md)`;
- **rewrites references** to the old filename in `docs/`, `decisions/`, `todo/` and
  `session-analysis/` in the same run;
- adds a legend under the index title;
- counts `awaiting-user` as **Live**.

`decisions/INDEX.md` is unchanged (todo only).

⭐ **Decision — §1:** ✅ nothing to decide.

## 2. Example

```
todo/🟢 T-050.md      ## 🟢 T-050 One repo · one process · one DB for repurpose
todo/✅ T-001.md      ## ✅ T-001 Repurpose stage …
todo/⏸️ T-003.md      ## ⏸️ T-003 Add FILE HEADERs …
todo/⏳ T-011.md      ## ⏳ T-011 Ask MSIA …
```

## 3. Regenerated and verified

`python3 tools/build_register_indexes.py` →
`renamed=50; refs=54; live=6`.

- All **50** files renamed; **54** files had references rewritten (docs, decisions, todo, replies).
- Zero plain `todo/T-xxx.md` references remain.
- A second run reports `renamed=0; refs=0` — idempotent.
- Link check: only the two external references inside the 30-Oct transcript remain
  (`AGENDA.md`, the 30-Oct brief), which are not in this repo.

## 4. How it stays correct

Change `status:` in a file, run the generator: it renames the file, updates the heading, rewrites
the references and regenerates the index. The file name, heading and index can never disagree.

**Cost of this choice:** the path changes with the status, so any **external** link to
`todo/T-xxx.md` (outside this repo) will break, and emoji filenames need a UTF-8-safe filesystem
(Linux/macOS fine; Windows 10+ NTFS fine, older tooling may struggle). Inside the repo the generator
keeps everything consistent.
