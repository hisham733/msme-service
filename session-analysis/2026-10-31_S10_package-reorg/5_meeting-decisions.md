# 5 — next MSME meeting decision list

**Deliverable:** `docs/MEETING-DECISIONS-2026-11.md` (118 lines), linked from `docs/INDEX.md` and
`NOW.md` ("What the user owes").

## 1. What it contains

- **§1 settled** — 3R, score+threshold, reasons, link sources, embedded media, one pipeline,
  repurpose, "start simple" (do not re-ask).
- **§2 open MSME decisions** — `AG-16`, `AG-14`, `AG-12`, `AG-13`, `AG-09`, `M-1`…`M-6`, each with:
  what the system does today, what changes per option, owner, recommendation, what it blocks.
- **§3 technical decisions (EF)** — `B-1` threshold 60 vs 62, `B-2` political-advocacy inversion,
  `B-3` missing filter questions (events/awards first), `B-4` failure ≠ REJECT, `B-5` published-site
  gold set, `B-6` SEO image naming.
- **§4** recommended meeting order; **§5** where each change lands (repo/file); **§6** a copy-paste
  answer sheet; **§7** evidence; **§8** the missing-answers request.

## 2. The findings that matter most

| Finding | Why it matters |
|---|---|
| `AG-09` is **already built** (PDF/DOCX embedded media, D8/D24) | close it with evidence instead of re-scoping |
| Wayne's "start simple = attachments only" conflicts with the built link fetching | 5 of the 7 real examples depend on links; needs his confirmation (`M-1`) |
| Threshold is **60 here, 62 in the partner engine** | one number must win (`B-1`) |
| The partner measured `political_advocacy` as **inverted** | verify our battery before the next accuracy claim (`B-2`) |
| No dedicated **Events/Awards** question | their largest false-accept source (`B-3`) |
| Auto-reply currently goes to a **fixed test address** | go-live needs `REPLY_MODE=sender` + wording approval (`M-2`) |
| No daily report, no WordPress upload, no published-site dedupe | three explicit scope decisions (`M-3`, `M-4`, `AG-14`) |

⭐ **Decision — §2:** the answer sheet is ready for the call; the answers become `decisions/D39+`
and `todo/` items afterwards.

## 3. Missing input

`NEXT_MEETING.md` says the 30-Oct call answered `AG-01`…`AG-08` and `AG-15` as `D-024`…`D-029`, but
those files are **not in the zip or the repo copy** (it stops at `D-023`). Send them and the image,
caption, naming and AI-image rows can be closed instead of looking open.

## 4. What I recommend next

Hold the meeting in the order in §4; answer `AG-09`, `M-1`, `M-2`, `B-1` first (four one-line
answers that change live behaviour). After the answers: one `decisions/D39+` per ruling and one
`todo/T-049+` per change. Thinking effort: **low** to record, **medium** to implement.
