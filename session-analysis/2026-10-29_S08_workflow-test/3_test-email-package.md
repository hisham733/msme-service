# Test email package — Tenun Nusantara (send manually)

**Session:** 2026-10-29 · S08
**Folder:** `data/test_email_tenun_nusantara/`
**State:** ready to send; nothing injected, nothing sent.

## 1. What is in the folder

| File | Size | Purpose |
|---|---:|---|
| `press-release-tenun-nusantara.pdf` | 61 KB | The article (fake company, same accepted structure) |
| `press-release.txt` | 5.2 KB | Readable article text |
| `tnc-logo.png` | 6 KB | 600×200 placeholder logo; filename contains “logo” |
| `tnc-photo.jpg` | 1.1 MB | 2400×3000, above the 1 MB attached-photo floor |
| `email-body.txt` | 300 B | Cover note |
| `email.eml` | 1.6 MB | Optional ready MIME with the three attachments |
| `README.md` | 1.5 KB | The same instructions |

Fake company: **Tenun Nusantara Collective (TNC)** — `Rumah Tenun`, `www.tenunnusantara.example`,
`hello@tenunnusantara.example`, manager **Nur Aisyah Rahman**, dateline **29 October 2026**,
applications close **13 November 2026**. The PDF is synthetic and not for publication.

✅ nothing to decide.

## 2. Send it manually

- **To:** `ainews.msme@gmail.com`
- **Subject:**
  `Fwd: OPEN CALL - Tenun Nusantara Collective Seeks 10 Malaysian Fashion Practitioners for Its Inaugural Cohort`
- **Attach:** `press-release-tenun-nusantara.pdf`, `tnc-logo.png`, `tnc-photo.jpg`
- **Body** (`email-body.txt`):

```
Hi,

Sharing this open call for consideration. The full press release is attached, together with the logo and one photo.

Tenun Nusantara Collective is inviting 10 Malaysian fashion practitioners to its inaugural six-month incubator cohort. Applications close on 13 November 2026.

Thanks,
Test Desk
```

Send from your own address. `email.eml` is only a backup; its `From` is `test@example.com`.

✅ nothing to decide.

## 3. What should happen

1. Webhook/poll queues it; `all_emails/<subject>/` gets `article.md`, `images/`, `originals/`.
2. Checklist row: `hasArticle=true`, `hasPic=true`, `hasLogo=true`, `readyToFilter=true`.
3. Jev returns **ACCEPT**; `repurpose_export` copies it to `repurpose_inbox/<subject>/`.
4. The running worker creates `draft.md`/`run.json` (`validated`) and rebuilds `repurpose_site`.
5. `/editor.html` shows **Publish: ready** + **Open local draft**; the DLW page
   `http://localhost:8765/dlw/index.html` lists the new article (29 October 2026, near the top).

**Scope:** this proves **Published Locally / DLW**. The real WordPress uploader is still a
stub, so the live MSME site is not touched.

✅ nothing to decide.

## 4. What I need next

Send the email, then tell me **“sent”**. I will verify, in order: webhook/queue logs → checklist
flags → Jev outcome → `repurpose_inbox`/`run.json` → editor item and local draft → DLW entry.
If Jev rejects it, the editor shows the reason and we adjust the package.

✅ nothing to decide.

## What I recommend next

Send now and stay in this session; the verification is a short read of logs + DB + the two
pages, **low thinking effort**. There is no need to touch the engine or the live site.

## Recap

| Item | State |
|---|---|
| Package | Ready in `data/test_email_tenun_nusantara/` |
| PDF / logo / photo | 61 KB / 600×200 / 1.1 MB |
| Send method | Manual, to `ainews.msme@gmail.com` |
| Expected filter | ACCEPT |
| Expected output | Published Locally + DLW entry |
| Live WordPress | Not touched (uploader stub) |
