# Suggested fixes added to the meeting runbook

**Session:** 2026-10-29 · S08 · reply 14
**File:** `docs/meeting-2026-10-29/meeting.md` (139 lines)

## 1. What was added

A new **§5 Suggested fixes — for their decision**, plus a first line in §6 asking MSME to agree
with the direction. The page-by-page script is unchanged.

| Problem | Suggested fix | Effect |
|---|---|---|
| Ant CEO speech accepted | **Article-type review** — speech/op-ed/global thought leadership → editor review | Ant speech reviewed; the **Ant product** article stays accepted |
| BWH accepted | **SME relevance floor** `< 0.50` → editor review | BWH 0.45, AI Muda 0.41, Egon 0.43 reviewed; all current relevant ACCEPTs are above 0.50 |
| Global brand/consumer/luxury | **Site-fit review** — review, not hard reject | BWH and Mercedes judged by the editor |
| Event Me Now rejected | **Commercial review band** — product launch with high source/substance → review; hard sell stays reject | MSME can publish the product launch; a discount/hard sell still stops |
| One Malaysia example | **Local-development check** — one local mention is a review signal | Ant/BWH reviewed; real Malaysia developments still accepted |
| No labels | **Feedback loop + gold set** — editor buttons, 20–50 labelled emails, versioned config | Tune from MSME’s own decisions |
| Media gaps | **Media standard** — high-res photo/logo, Drive download, no tracking pixels, one release; count attached photos by dimensions (T-024), support HEIC | Fewer no-image accepts; the 11 sender asks |

The key line in the runbook:

> “We suggest these small changes: article-type review, an SME relevance review floor, a site-fit
> review, a commercial review band, and a feedback loop. None of these new rules auto-reject; the
> editor decides. The 3R safety gates still reject.”

✅ nothing to decide.

## 2. Why these fixes fit the evidence

- **Ant** has SME 0.86 but is a global CEO speech; the **article-type review** catches it. Its
  **product** article (MSME published) stays product/news, so it is not harmed.
- **BWH** has SME 0.45 and overall 0.57; the **SME floor 0.50 → review** catches it; the current
  relevant accepts are all above 0.50.
- **Event Me Now** and **Mercedes** are the opposite: hard gates fired, but MSME published them.
  The **commercial review band** and **site-fit review** stop silent false rejects.
- The **gold set + feedback loop** is the only way to set the thresholds from MSME’s own labels;
  every filter change is already versioned.

✅ nothing to decide.

## 3. Unchanged state

- **149 tests pass**; the password change is fixed and verified on localhost.
- The public hostname `hook.empi.site` is not resolving from this machine; for the Teams meeting
  use **`http://localhost:8899`** in screen share.
- Gmail OAuth is still expired; the demo uses the existing Tenun article.
- No code or data change in this turn; the meeting runbook is the only file updated.

✅ nothing to decide.

## 4. What I recommend next

In the meeting, show the runbook’s page table, then §5, and ask MSME to agree with the direction.
After the meeting, send me their **3 publish + 3 do-not-publish examples** and the exact
**rejected-but-published** articles; I will implement the approved rules as versioned filter
config versions.

## Recap

| Item | State |
|---|---|
| Runbook | Updated with suggested fixes |
| Suggested rules | Article type, SME floor, site fit, commercial band, local signal, feedback loop, media |
| Auto-reject risk | New rules are review-only; 3R gates still reject |
| Tests | 149 pass |
| Meeting | Today 10:30 MYT, Teams; use localhost screen share |
