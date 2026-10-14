# Baseball Scoring API

```bash
docker compose up -d            # MySQL
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload   # docs at http://localhost:8000/docs
```

For an existing database created before Alembic was introduced, back it up first,
then mark the legacy schema as the baseline and apply the scorer migration:

```bash
alembic stamp 0001_baseline
alembic upgrade head
```

Do not stamp a fresh database; `alembic upgrade head` creates its schema. If the
database already has the scorer table and `games.scorer_id`, use `alembic stamp head`
instead of reapplying the scorer migration.

Create scorer profiles with `POST /scorers` using `{"display_name": "Alex Smith"}`.
Pass the returned `scorer_id` when creating a game to record who scored it; scorer
profiles can be listed with `GET /scorers`. Games may omit `scorer_id`.
