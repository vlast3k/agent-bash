"""Unit tests for file_write tool."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


def test_successful_write(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.file_write import file_write
    result = file_write.invoke({"path": "output.txt", "content": "written content"})
    assert "written successfully" in result.lower() or "output.txt" in result
    assert (tmp_path / "output.txt").read_text() == "written content"


def test_path_traversal_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.file_write import file_write
    result = file_write.invoke({"path": "../../tmp/evil.sh", "content": "rm -rf /"})
    assert "denied" in result.lower() or "outside" in result.lower()


def test_sibling_directory_prefix_collision_rejected(tmp_path, monkeypatch):
    """C1: Sibling-directory prefix collision must be rejected on writes too."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    evil_dir = tmp_path / "sandbox-evil"
    evil_dir.mkdir()
    monkeypatch.setenv("SANDBOX_WORKDIR", str(sandbox))
    from tools.file_write import file_write
    result = file_write.invoke({"path": "../sandbox-evil/pwned.txt", "content": "bad"})
    assert "denied" in result.lower() or "outside" in result.lower()
    assert not (evil_dir / "pwned.txt").exists()


def test_directory_creation(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.file_write import file_write
    result = file_write.invoke({"path": "subdir/nested/file.txt", "content": "nested"})
    assert (tmp_path / "subdir" / "nested" / "file.txt").exists()
    assert (tmp_path / "subdir" / "nested" / "file.txt").read_text() == "nested"


def test_overwrite_existing_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    (tmp_path / "existing.txt").write_text("old content")
    from tools.file_write import file_write
    file_write.invoke({"path": "existing.txt", "content": "new content"})
    assert (tmp_path / "existing.txt").read_text() == "new content"


def test_disk_exhaustion_prevented(tmp_path, monkeypatch):
    """H1: Writes exceeding 10 MiB must be rejected."""
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.file_write import file_write
    huge = "x" * (11 * 1024 * 1024)   # 11 MiB
    result = file_write.invoke({"path": "huge.bin", "content": huge})
    assert "too large" in result.lower() or "maximum" in result.lower()
    assert not (tmp_path / "huge.bin").exists()
