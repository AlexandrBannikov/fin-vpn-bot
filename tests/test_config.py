import importlib

import pytest

import app.config as config


def test_get_env_int_returns_default_for_missing_or_empty_value(monkeypatch):
    monkeypatch.delenv("TEST_INT", raising=False)
    assert config.get_env_int("TEST_INT", 42) == 42

    monkeypatch.setenv("TEST_INT", "  ")
    assert config.get_env_int("TEST_INT", 42) == 42


def test_get_env_int_parses_value_and_reports_invalid_value(monkeypatch):
    monkeypatch.setenv("TEST_INT", " 7 ")
    assert config.get_env_int("TEST_INT", 42) == 7

    monkeypatch.setenv("TEST_INT", "seven")
    with pytest.raises(ValueError, match="TEST_INT must be an integer"):
        config.get_env_int("TEST_INT", 42)


def test_get_env_bool_handles_default_and_truthy_values(monkeypatch):
    monkeypatch.delenv("TEST_BOOL", raising=False)
    assert config.get_env_bool("TEST_BOOL", True) is True

    monkeypatch.setenv("TEST_BOOL", "  ")
    assert config.get_env_bool("TEST_BOOL", False) is False

    monkeypatch.setenv("TEST_BOOL", "yes")
    assert config.get_env_bool("TEST_BOOL", False) is True

    monkeypatch.setenv("TEST_BOOL", "0")
    assert config.get_env_bool("TEST_BOOL", True) is False


def test_restart_command_is_split_from_environment(monkeypatch):
    monkeypatch.setenv("XUI_RESTART_COMMAND", "service x-ui restart")

    reloaded_config = importlib.reload(config)

    assert reloaded_config.XUI_RESTART_COMMAND == ["service", "x-ui", "restart"]
