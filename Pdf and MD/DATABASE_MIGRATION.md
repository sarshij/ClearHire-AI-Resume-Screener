# DATABASE_MIGRATION.md
## SQLite → PostgreSQL Migration Record

---

### Summary

This migration replaces the SQLite database backend with PostgreSQL.
The application used `SQLAlchemy 2.x (async)` with `aiosqlite` as the async driver.
It now uses `asyncpg` as the async driver for PostgreSQL.

All models, CRUD helpers, session factories, and business logic remain **100% unchanged**.
Only the database connection layer was modified.

---

### Files Modified

| File | Type | Reason |
|------|------|---------|
| `app/models/database.py` | Modified | Replace SQLite URL + driver with PostgreSQL |
| `requirements.txt` | Modified | Remove `aiosqlite`, add `asyncpg` + `psycopg2-binary` |
| `Dockerfile` | Modified | Remove SQLite data dir, add PostgreSQL ENV defaults |
| `.env.example` | **New** | Document required environment variables |
| `DATABASE_MIGRATION.md` | **New** | This file |
| `README.md` | Modified | Added "PostgreSQL Migration" section |

---

### What Changed in Each File

#### `app/models/database.py`

**Removed:**
```python
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'resume_screener.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
```

**Added:**
```python
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    pg_host     = os.environ.get("POSTGRES_HOST",     "localhost")
    pg_port     = os.environ.get("POSTGRES_PORT",     "5432")
    pg_db       = os.environ.get("POSTGRES_DB",       "resume_screener")
    pg_user     = os.environ.get("POSTGRES_USER",     "postgres")
    pg_password = os.environ.get("POSTGRES_PASSWORD", "")
    DATABASE_URL = f"postgresql+asyncpg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
```

**Also added** `pool_pre_ping=True` to the engine – detects stale connections before use (best practice for PostgreSQL).

**Not changed:** `JobDescription` model, `ResumeAnalysis` model, `Base`, `init_db()`, `get_db()`, `async_session`.

---

#### `requirements.txt`

**Removed:** `aiosqlite>=0.19.0` — SQLite async driver, no longer needed.

**Added:**
- `asyncpg>=0.29.0` — async PostgreSQL driver used by SQLAlchemy.
- `psycopg2-binary>=2.9.9` — sync driver; useful for Alembic migrations and DB tooling.

---

#### `Dockerfile`

**Removed:** `RUN mkdir -p logs data scratch` → `RUN mkdir -p logs scratch`
(The `data/` directory held the SQLite file. PostgreSQL is an external service.)

**Added:** Default `ENV` entries for PostgreSQL connection variables. These are overridden at runtime via `docker run -e` or `docker-compose.yml`.

---

#### `.env.example` (new)

Documents all environment variables required for the database connection. Copy to `.env` and fill in real values. `.env` is already git-ignored.

---

### Why the Change Was Necessary

| Detail | Explanation |
|--------|-------------|
| Driver swap | `aiosqlite` only works with SQLite. PostgreSQL requires `asyncpg` (async) or `psycopg2` (sync). |
| URL scheme | SQLAlchemy uses `sqlite+aiosqlite:///` vs `postgresql+asyncpg://` — driver is embedded in the URL. |
| Connection pooling | SQLite uses a file path; PostgreSQL uses a network host/port. `pool_pre_ping` added to handle network drops. |
| Data directory | SQLite needed a writable `data/` dir. PostgreSQL is an external service — the dir is no longer required. |

---

### Assumptions Made

1. PostgreSQL ≥ 13 is installed and accessible on the host defined by env vars.
2. The target database (`resume_screener` by default) already exists, OR the PostgreSQL user has `CREATEDB` privilege (so `init_db()` can auto-create tables via `CREATE TABLE IF NOT EXISTS`).
3. No existing SQLite data needs to be preserved (user confirmed this).
4. The SQLAlchemy models are already PostgreSQL-compatible — `JSON`, `Text`, `Float`, `DateTime(timezone=True)`, `Integer` all map natively to PostgreSQL types.

---

### Manual Steps Required Before Starting the App

```powershell
# 1. Install new Python dependencies
pip install asyncpg psycopg2-binary

# 2. Create the database in PostgreSQL (if it doesn't exist yet)
#    Connect to PostgreSQL as a superuser and run:
#    CREATE DATABASE resume_screener;

# 3. Set environment variables (choose one method):

# Method A – Set in PowerShell session (temporary, for testing)
$env:POSTGRES_HOST     = "localhost"
$env:POSTGRES_PORT     = "5432"
$env:POSTGRES_DB       = "resume_screener"
$env:POSTGRES_USER     = "postgres"
$env:POSTGRES_PASSWORD = "your_password"

# Method B – Copy .env.example to .env and fill in values
#    (requires python-dotenv or loading .env before starting the app)

# 4. Start the application
python app/main.py
# Tables are auto-created on first startup via init_db()
```

---

### Switching to a Different Machine (e.g. a friend's laptop)

Only update the environment variables — no code change needed:

```powershell
$env:POSTGRES_HOST     = "friends-machine-ip-or-hostname"
$env:POSTGRES_PASSWORD = "their_password"
$env:POSTGRES_USER     = "their_user"    # if different
$env:POSTGRES_DB       = "resume_screener"
```

Or set `DATABASE_URL` directly:
```powershell
$env:DATABASE_URL = "postgresql+asyncpg://user:password@host:5432/resume_screener"
```

---

### Known Limitations

1. **No Alembic / migration tooling** — schema is managed via `Base.metadata.create_all`. If the schema changes in the future, tables will need to be dropped and recreated manually or Alembic should be introduced.
2. **No data migration** — the existing SQLite `data/resume_screener.db` records are not transferred. PostgreSQL starts with an empty database.
3. **POSTGRES_PASSWORD has no default** — the app will log a warning and likely fail to connect if this variable is not set.

---

### Confirmed Unchanged

The following areas were **not modified** in any way:

- All routes (`/api/predict`, `/api/predict_batch`, `/api/history`, `/api/export`, `/health`, `/login`, `/logout`, etc.)
- Authentication flow (`USERS` dict, session middleware)
- Resume upload and parsing (`app/utils/parser.py`)
- NLP preprocessing (`app/utils/nlp.py`)
- Validation logic (`app/features/validation.py`)
- XGBoost classifier (`app/models/classifier.py`)
- SBERT embedder (`app/models/embedder.py`)
- All frontend templates and static files
- Folder structure and file naming
- Coding style and comment style
