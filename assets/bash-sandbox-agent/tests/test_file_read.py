"""Unit tests for file_read tool."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


def test_successful_read(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    (tmp_path / "hello.txt").write_text("file content here")
    from tools.file_read import file_read
    result = file_read.invoke({"path": "hello.txt"})
    assert "file content here" in result


def test_path_traversal_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.file_read import file_read
    result = file_read.invoke({"path": "../../etc/passwd"})
    assert "denied" in result.lower() or "outside" in result.lower()


def test_sibling_directory_prefix_collision_rejected(tmp_path, monkeypatch):
    """C1: A sibling dir that shares the sandbox prefix string must be rejected.

    e.g. sandbox=/tmp/abc  →  /tmp/abc-evil passes startswith('/tmp/abc') but
    must be rejected by is_relative_to().
    """
    import tempfile
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    evil_dir = tmp_path / "sandbox-evil"
    evil_dir.mkdir()
    secret = evil_dir / "secret.txt"
    secret.write_text("stolen")
    monkeypatch.setenv("SANDBOX_WORKDIR", str(sandbox))
    from tools.file_read import file_read
    result = file_read.invoke({"path": "../sandbox-evil/secret.txt"})
    assert "denied" in result.lower() or "outside" in result.lower()
    assert "stolen" not in result


def test_missing_file_error(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.file_read import file_read
    result = file_read.invoke({"path": "nonexistent.txt"})
    assert "does not exist" in result.lower() or "error" in result.lower()


def test_output_truncation(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    (tmp_path / "big.txt").write_text("x" * 9000)
    from tools.file_read import file_read
    result = file_read.invoke({"path": "big.txt"})
    assert "truncated" in result or len(result) <= 8200
