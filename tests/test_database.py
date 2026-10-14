from app import database


class FakeSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_get_db_closes_session_when_generator_finishes(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(database, "SessionLocal", lambda: session)

    db_dependency = database.get_db()
    assert next(db_dependency) is session
    db_dependency.close()

    assert session.closed