import pytest

import scripts.migrate as migrate_script


def test_migrate_script_prints_applied_migrations(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "bot.db"
    monkeypatch.setattr(migrate_script, "BOT_DB_PATH", str(db_path))

    migrate_script.main()

    output = capsys.readouterr().out
    assert "Applied migrations:" in output
    assert "001_create_core_tables" in output


def test_migrate_script_prints_no_pending_migrations(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "bot.db"
    monkeypatch.setattr(migrate_script, "BOT_DB_PATH", str(db_path))

    migrate_script.main()
    capsys.readouterr()

    migrate_script.main()

    assert capsys.readouterr().out == "No pending migrations.\n"


def test_migrate_script_exits_when_database_directory_is_missing(monkeypatch):
    monkeypatch.setattr(
        migrate_script,
        "BOT_DB_PATH",
        "/no/such/folder/bot.db",
    )

    with pytest.raises(SystemExit) as exc:
        migrate_script.main()

    assert "Database directory does not exist" in str(exc.value)
