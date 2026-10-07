"""Unit tests for python_exec tool."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


def test_successful_execution(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.python_exec import python_exec
    result = python_exec.invoke({"code": "print('hello world')"})
    assert "hello world" in result


def test_stderr_captured(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.python_exec import python_exec
    result = python_exec.invoke({"code": "import sys; sys.stderr.write('err_msg')"})
    assert "err_msg" in result


def test_syntax_error_captured(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.python_exec import python_exec
    result = python_exec.invoke({"code": "def f(:"})
    assert result  # returns something (error message)


def test_timeout_handling(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("PYTHON_EXEC_TIMEOUT", "1")
    from tools.python_exec import python_exec
    result = python_exec.invoke({"code": "import time; time.sleep(10)"})
    assert "timed out" in result.lower()


def test_output_truncation(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.python_exec import python_exec
    result = python_exec.invoke({"code": "print('x' * 9000)"})
    assert "truncated" in result or len(result) <= 8200


def test_aicore_credentials_not_forwarded(tmp_path, monkeypatch):
    """H3 fix: AICORE_* env vars must NOT be visible inside the subprocess."""
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("AICORE_CLIENT_ID", "super-secret-token")
    from tools.python_exec import python_exec
    result = python_exec.invoke({
        "code": "import os; print(os.environ.get('AICORE_CLIENT_ID', 'NOT_FOUND'))"
    })
    assert "super-secret-token" not in result
    assert "NOT_FOUND" in result


def test_sap_credentials_not_forwarded(tmp_path, monkeypatch):
    """H3 fix: SAP_* env vars must NOT be visible inside the subprocess."""
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("SAP_SERVICE_KEY", "sap-secret-value")
    from tools.python_exec import python_exec
    result = python_exec.invoke({
        "code": "import os; print(os.environ.get('SAP_SERVICE_KEY', 'NOT_FOUND'))"
    })
    assert "sap-secret-value" not in result
    assert "NOT_FOUND" in result
