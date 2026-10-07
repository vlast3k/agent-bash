"""Unit tests for shell_exec tool."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


def test_allowlisted_command_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("SHELL_ALLOWLIST", "echo,ls")
    from tools.shell_exec import shell_exec
    result = shell_exec.invoke({"command": "echo hello"})
    assert "hello" in result


def test_blocked_command_returns_refusal(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("SHELL_ALLOWLIST", "echo")
    from tools.shell_exec import shell_exec
    result = shell_exec.invoke({"command": "rm -rf /"})
    assert "not allowed" in result.lower()


def test_output_truncation(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("SHELL_ALLOWLIST", "python3")
    from tools.shell_exec import shell_exec
    result = shell_exec.invoke({"command": "python3 -c \"print('x' * 9000)\""})
    assert "truncated" in result or len(result) <= 8200


def test_empty_command(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.shell_exec import shell_exec
    result = shell_exec.invoke({"command": ""})
    assert "empty" in result.lower()


def test_ls_lists_files(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("SHELL_ALLOWLIST", "ls")
    (tmp_path / "testfile.txt").write_text("hello")
    from tools.shell_exec import shell_exec
    result = shell_exec.invoke({"command": "ls"})
    assert "testfile.txt" in result


# --- Security: argument validation (C2 fixes) ---

def test_shell_meta_character_in_arg_rejected(tmp_path, monkeypatch):
    """Shell meta-characters in arguments must be rejected (injection guard)."""
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("SHELL_ALLOWLIST", "echo")
    from tools.shell_exec import shell_exec
    result = shell_exec.invoke({"command": "echo hello; rm -rf /"})
    assert "rejected" in result.lower() or "not allowed" in result.lower()


def test_absolute_path_outside_sandbox_rejected(tmp_path, monkeypatch):
    """Absolute paths outside the sandbox must be rejected."""
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("SHELL_ALLOWLIST", "cat")
    from tools.shell_exec import shell_exec
    result = shell_exec.invoke({"command": "cat /etc/passwd"})
    assert "rejected" in result.lower() or "outside" in result.lower()


def test_backtick_injection_rejected(tmp_path, monkeypatch):
    """Backtick command substitution must be rejected."""
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("SHELL_ALLOWLIST", "echo")
    from tools.shell_exec import shell_exec
    result = shell_exec.invoke({"command": "echo `id`"})
    assert "rejected" in result.lower() or "forbidden" in result.lower()


def test_find_exec_rejected(tmp_path, monkeypatch):
    """find -exec must be rejected."""
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("SHELL_ALLOWLIST", "find")
    from tools.shell_exec import shell_exec
    result = shell_exec.invoke({"command": "find . -name '*.py' -exec cat {} \\;"})
    assert "rejected" in result.lower() or "forbidden" in result.lower()
