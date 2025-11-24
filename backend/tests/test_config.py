from backend.app import config


def test_secret_key_fallback():
    assert isinstance(config.settings.secret_key, str)
    assert config.settings.secret_key != ""

