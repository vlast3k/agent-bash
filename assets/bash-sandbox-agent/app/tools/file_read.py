"""File read tool — reads files scoped to the sandbox working directory."""
import os
from pathlib import Path
from langchain_core.tools import tool
from tools.sanitiser import sanitise

_MAX_OUTPUT = 8000


def _resolve_path(path: str) -> tuple[Path, str | None]:
    """Resolve path relative to SANDBOX_WORKDIR; return (resolved, error_msg).

    Uses Path.is_relative_to() (Python 3.9+) instead of a startswith() string
    check to prevent the prefix-collision bypass where a sibling directory such
    as '/tmp/agent-sandbox-evil' would pass a plain string prefix test.
    Symlinks are fully followed by Path.resolve() before the check, preventing
    symlink-escape attacks.
    """
    workdir = Path(os.environ.get("SANDBOX_WORKDIR", "/tmp/agent-sandbox")).resolve()
    os.makedirs(workdir, exist_ok=True)
    resolved = (workdir / path).resolve()
    # is_relative_to() requires the resolved path to be *inside* workdir,
    # not merely to share a string prefix with it.
    if not (resolved == workdir or resolved.is_relative_to(workdir)):
        return resolved, f"Access denied: path '{path}' resolves outside the sandbox."
    return resolved, None


@tool
def file_read(path: str) -> str:
    """Read the contents of a file inside the sandbox working directory.

    Args:
        path: Path to the file (relative to the sandbox working directory).

    Returns:
        File contents as a string.
    """
    resolved, err = _resolve_path(path)
    if err:
        return err

    if not resolved.exists():
        return f"Error: file '{path}' does not exist."
    if not resolved.is_file():
        return f"Error: '{path}' is not a file."

    try:
        content = resolved.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error reading file: {e}"

    content = sanitise(content)
    if len(content) > _MAX_OUTPUT:
        content = content[:_MAX_OUTPUT] + f"\n[Output truncated at {_MAX_OUTPUT} characters]"
    return content
