import sqlite3

import pytest


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


@pytest.fixture(autouse=True)
def close_sqlite_connections(monkeypatch):
    original_connect = sqlite3.connect

    def connect(*args, **kwargs):
        kwargs.setdefault("factory", ClosingConnection)
        return original_connect(*args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", connect)
