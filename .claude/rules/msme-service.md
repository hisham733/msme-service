# msme-service work rules (always loaded)

- **Verify before asserting** — the live system is checked by running it (`python3 -m compileall -q msme run.py tools tests`;
  `curl -s localhost:8899/health`); a state not measured this session is unknown.
- **Registers graduate facts**: a decision → `decisions/<id>.md`; open work → `todo/<id>.md`. After edits
  run `python3 tools/build_register_indexes.py`.
- **Build and test together.** Every script change names the run that proves it, or says why none.
- **One entrypoint on :8899**: `run.py` → `msme/combined.py`, which dispatches to `msme/receive/dashboard.py`
  (receive) and `msme/filtering/filter_service.py` (filter). `msme/legacy/main.py` / `:8898` are legacy and
  not started. A page belongs to the app in `static/INDEX.md` — change the right one.
- **File headers are a contract**: keep the `FILE HEADER` block in every website-runtime `.py` accurate
  when you change its role, imports or callers (`decisions/D2.md`).
- **Secrets and live data stay out of git and out of replies**: `creds/`, `data/`, `emails/`, `all_emails/`,
  and never print a key or token.
- **Repurpose is external** — the `MSME_AI_News` engine on :8765 (D35); never rebuild it here.
- **Auth boundary (T-047)**: `combined.py` wraps the app in `auth.AuthGate`. Public paths are
  `/health`, `/login`, `/api/auth/login`, `/webhooks/gmail`, `/auth.js`. Admin/editor rules live in
  `auth.evaluate` — never add a public path without a reason; test with `tests/test_auth.py`.
- **Pre-reply checklist**: route every fact to its home · regenerate indexes · name the proving run ·
  write the reply file; chat = the summary only.
