# Not-ready recommendations executed — 9 resolved, 17 remain

**Session:** 2026-10-22_S02 · **Turn:** 11 · **Image:** `msme-service:batch-3-20261022`
**Report:** `docs/NOT-READY-TO-FILTER-2026-10-22.md` · **Asks:** `docs/SENDER-ASKS-2026-10-22.md`

---

## 1. Re-runs — 9 of 9 now ready

| Email | Result |
|---|---|
| Sanct Social | `hasPic=true` (4 inline photos) |
| PIKOM | subject 90; embedded logo |
| ICAEW | subject 89; embedded logo |
| AiSEM | D12 picked the **Media Statement**; subject 80; photos |
| Hotcoin | `hasPic=true` (4 inline photos) |
| **redBus** | subject 95; **new bug found and fixed**: the Drive image `redBus - Krishnan.jpg` (8.7 MB) was treated as an article source and marked `needs_human`; now media → `hasPic=true`, ready (`D13`/`T-023`) |
| Data centers | subject 75 (new prompt); logo |
| MICSEA | subject 88 (new prompt); logo + image |
| EY | subject 85 (new prompt); photo + image |

Deployed and verified live: `hasArticle=true`, `readyToFilter=true`, health OK on `:8898`/`:8899`/`:8900`.

⭐ **Decision — §1:** ✅ nothing to decide.

---

## 2. Remaining 17

| Group | Count | Action |
|---|--:|---|
| No qualifying media | **9** | 10 asks drafted below (9 media + i-City) |
| Not a press release | 6 | ignore for filtering |
| Source not retrievable | 2 | MSIA (`T-011`) + i-City (folder still **0 docs/0 images**) |

The 9 no-media rows: WhatsApp article, IMAGO, Event Me Now, ICW, Trainocate, Jobstreet, Anak Sulung,
Research pitch, Mimecast. The 6 non-releases: 2 Google notifications, EnerGex invite, Budget POV pitch,
World Bank speech advisory, EAP report package.

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. What you need to send

`docs/SENDER-ASKS-2026-10-22.md` has the recipients, the missing asset and a ready-to-send text for each:

- **9 media asks:** WhatsApp (Vishesh), IMAGO (hello@imago.us), Event Me Now (Murali), ICW (ashton@qube),
  Trainocate (ned.wee), Jobstreet (Niraen), Anak Sulung (Jane Teo), Research pitch (Jinn), Mimecast (Yazid).
- **1 access ask:** i-City (Syuhaida) — the Drive folder still returns nothing.
- **MSIA** (`T-011`): the Drive PDF is still view-only (`dayana.arif@msia.org.my`).

Nothing was sent automatically (`REPLY_ENABLED=false`).

⭐ **Decision — §3:** ✅ nothing to decide (send when ready).

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Recommended re-runs | **9/9 ready** |
| 2 | New Drive-image bug | fixed + live (`D13`/`T-023`) |
| 3 | Not-ready list | 26 → **17** |
| 4 | Sender asks | 10 drafted, awaiting you |
| 5 | i-City Drive | still empty — access ask drafted |

## What I recommend next

Send the 10 asks + the MSIA request. When a sender replies, re-run that email (no code expected). The next
build remains **T-001 (repurpose)** — new session, medium effort.
