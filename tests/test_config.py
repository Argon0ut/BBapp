import importlib

import src.config as config_module


def _reload_config():
    importlib.reload(config_module)
    config_module.get_settings.cache_clear()
    return config_module


def test_settings_prefer_standard_aws_env_names(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY", "stale-access-key")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "correct-access-key")
    monkeypatch.setenv("AWS_SECRET_KEY", "stale-secret-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "correct-secret-key")
    monkeypatch.setenv("AWS_REGION", " eu-north-1 ")
    monkeypatch.setenv("AWS_BUCKET_NAME", " \"bb-app-s3\" ")

    config = _reload_config()
    settings = config.get_settings()

    assert settings.aws_access_key == "correct-access-key"
    assert settings.aws_secret_key == "correct-secret-key"
    assert settings.aws_region == "eu-north-1"
    assert settings.aws_bucket_name == "bb-app-s3"


def test_settings_fall_back_to_legacy_aws_env_names(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY", "legacy-access-key")
    monkeypatch.setenv("AWS_SECRET_KEY", "legacy-secret-key")
    monkeypatch.setenv("AWS_SESSION_TOKEN", " token-value ")

    config = _reload_config()
    settings = config.get_settings()

    assert settings.aws_access_key == "legacy-access-key"
    assert settings.aws_secret_key == "legacy-secret-key"
    assert settings.aws_session_token == "token-value"
