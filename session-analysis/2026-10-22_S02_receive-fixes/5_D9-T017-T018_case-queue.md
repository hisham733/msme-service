# Aventra logged — case queue opened, no code yet

**Session:** 2026-10-22_S02 · **Turn:** 5 · **IDs:** D9 · T-017 · T-018

---

## 1. Aventra — what was missed (measured)

| Check | Result |
|---|---|
| Attachments | 0 |
| Article | full release in the body; `hasArticle=true`, subjectScore 100 |
| Body images | 2 Aventra **vertical-logo** thumbnails (264×277, 270×284) + 3 social icons (64×64) |
| "Click to download" | `media-outreach.com/i/Download/818162` → **1220×1281 PNG**, filename **"Aventra Group Vertical Logo.png"** |
| Why every flag is false | no photo exists; D7 keeps only `kind=photo`, and a logo has no column today |
| Row | `hasPic=false`, `hasLogo=false`, `hasLogoInArticle=false`, `readyToFilter=false` |

⭐ **Decision — §1:** ✅ nothing to decide (rule agreed: `D9`).

---

## 2. What I logged — no code changed, no deploy

| Register | Content |
|---|---|
| `decisions/D9.md` | body/downloaded logos count as `hasLogo` (never `hasPic`); filename hint beats dimensions; full-res asset replaces the thumbnail |
| `todo/✅ T-017.md` | the Aventra build — status **`decided-unbuilt`**, waits for the batch |
| `todo/✅ T-018.md` | **case queue** with every report so far and the protocol |

Current queue:

| Case | Missed | Cause | State |
|---|---|---|---|
| MSIA | article | Drive file view-only | fixed + live |
| IRGCE | picture | 5 inline body photos | fixed + live |
| ACCA | logo | vector PDF header logo | fixed + live |
| **Aventra** | picture/logo | body logo + full-res `/Download/` link | **logged** |

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. How the next cases go

1. You send the next "no article / no pic / no logo" email.
2. I measure it, add one row to `T-018`, and reply with the queue only.
3. When you say **"list complete"**, I build every `logged` row in **one batch**, deploy once, and write
   one verification reply.

*Nothing was changed in the running service this turn.*

⭐ **Decision — §3:** ✅ nothing to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Aventra cause | measured: logo, no photo |
| 2 | Rule for logos | `D9` decided |
| 3 | Aventra build | `T-017` decided-unbuilt |
| 4 | Batch protocol | `T-018` open |

## What I recommend next

Send the remaining cases. When you are done, say **"list complete"** — then start the batch in this
session at **medium** effort (one code pass, one deploy, one reply).

> Ready-to-paste when done: `list complete — build every logged row in T-018 in one batch.`
