# msme-service work rules (always loaded)

- **Verify before asserting** — the live system is checked by running it (`python3 -m compileall -q *.py`;
  `curl -s localhost:8898/health` / `localhost:8900/health`); a state not measured this session is unknown.
- **Registers graduate facts**: a decision → `decisions/<id>.md`; open work → `todo/<id>.md`. After edits
  run `python3 tools/build_register_indexes.py`.
- **Build and test together.** Every script change names the run that proves it, or says why none.
- **Three apps, one entrypoint**: `run.py` starts API :8898 (`main.py`), dashboard :8899 (`dashboard.py`),
  filter :8900 (`filter_service.py`). A page belongs to the port in `static/INDEX.md` — change the right app.
- **File headers are a contract**: keep the `FILE HEADER` block in every website-runtime `.py` accurate
  when you change its role, imports or callers (`decisions/D2.md`).
- **Secrets and live data stay out of git and out of replies**: `creds/`, `data/`, `emails/`, `all_emails/`,
  and never print a key or token.
- **Repurpose is not built** — never describe it as working; work it only under `todo/T-001`.
- **Pre-reply checklist**: route every fact to its home · regenerate indexes · name the proving run ·
  write the reply file; chat = the summary only.
