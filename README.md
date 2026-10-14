# Baseball Scoring API

```bash
docker compose up -d            # MySQL
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload   # docs at http://localhost:8000/docs
```

Tables are created on startup. Switch to Alembic migrations before the schema stabilizes.
