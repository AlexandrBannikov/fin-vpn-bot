import sqlite3
import time
from collections.abc import Callable
from pathlib import Path

from app.db import connect_sqlite

Migration = tuple[str, Callable[[sqlite3.Connection], None]]


def table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {
        row[1]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }


def add_column_if_missing(
    conn: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    if column_name not in table_columns(conn, table_name):
        conn.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


def create_core_tables(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            vpn_email TEXT,
            referrer_id INTEGER,
            created_at INTEGER,
            subscription_started_at INTEGER,
            subscription_days INTEGER DEFAULT 30,
            subscription_status TEXT DEFAULT 'trial',
            last_warning_at INTEGER,
            role TEXT DEFAULT 'user'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL UNIQUE,
            created_at INTEGER
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS invite_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_tg_id INTEGER NOT NULL,
            vpn_email TEXT NOT NULL,
            sub_id TEXT NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created_at INTEGER NOT NULL,
            used_at INTEGER
        )
    """)


def add_subscription_columns(conn: sqlite3.Connection) -> None:
    add_column_if_missing(conn, "users", "subscription_started_at", "INTEGER")
    add_column_if_missing(conn, "users", "subscription_days", "INTEGER DEFAULT 30")
    add_column_if_missing(
        conn,
        "users",
        "subscription_status",
        "TEXT DEFAULT 'trial'",
    )
    add_column_if_missing(conn, "users", "last_warning_at", "INTEGER")


def add_user_role_column(conn: sqlite3.Connection) -> None:
    add_column_if_missing(conn, "users", "role", "TEXT DEFAULT 'user'")


def add_invite_link_columns(conn: sqlite3.Connection) -> None:
    add_column_if_missing(conn, "invite_links", "token", "TEXT")
    add_column_if_missing(conn, "invite_links", "used_at", "INTEGER")


MIGRATIONS: tuple[Migration, ...] = (
    ("001_create_core_tables", create_core_tables),
    ("002_add_subscription_columns", add_subscription_columns),
    ("003_add_user_role_column", add_user_role_column),
    ("004_add_invite_link_columns", add_invite_link_columns),
)


def ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at INTEGER NOT NULL
        )
    """)


def applied_versions(conn: sqlite3.Connection) -> set[str]:
    ensure_migration_table(conn)
    return {
        row[0]
        for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
    }


def apply_bot_migrations(db_path: str | Path) -> list[str]:
    applied: list[str] = []

    with connect_sqlite(db_path) as conn:
        ensure_migration_table(conn)
        existing_versions = applied_versions(conn)

        for version, migration in MIGRATIONS:
            if version in existing_versions:
                continue

            migration(conn)
            conn.execute(
                """
                INSERT INTO schema_migrations (version, applied_at)
                VALUES (?, ?)
                """,
                (version, int(time.time())),
            )
            applied.append(version)

        conn.commit()

    return applied
