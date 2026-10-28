# sql/ — INDEX

| File | Purpose |
|---|---|
| `schema_mysql.sql` | prepared MySQL schema for the future DB switch (`DB_ENGINE=mysql` + `MYSQL_DSN`); mirrors the SQLite tables in `db.py` |

No migration runner yet — SQLite (`data/msme.sqlite3`) is the live store.
