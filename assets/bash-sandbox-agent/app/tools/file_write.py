"""File write tool — creates or updates files inside the sandbox working directory."""
import os
from pathlib import Path
from langchain_core.tools import tool

_MAX_WRITE_BYTES = 10 * 1024 * 1024  # 10 MiB — prevent disk exhaustion


def _resolve_path(path: str) -> tuple[Path, str | None]:
    """Resolve path relative to SANDBOX_WORKDIR; return (resolved, error_msg).

    Uses Path.is_relative_to() (Python 3.9+) instead of a startswith() string
    check to prevent the prefix-collision bypass where a sibling directory such
    as '/tmp/agent-sandbox-evil' would pass a plain string prefix test.
    """
    workdir = Path(os.environ.get("SANDBOX_WORKDIR", "/tmp/agent-sandbox")).resolve()
    os.makedirs(workdir, exist_ok=True)
    resolved = (workdir / path).resolve()
    if not (resolved == workdir or resolved.is_relative_to(workdir)):
        return resolved, f"Access denied: path '{path}' resolves outside the sandbox."
    return resolved, None


@tool
def file_write(path: str, content: str) -> str:
    """Write content to a file inside the sandbox working directory.
    Creates the file and any missing parent directories if they do not exist.

    Args:
        path: Path to the file (relative to the sandbox working directory).
        content: Content to write to the file.

    Returns:
        Confirmation message with the resolved file path.
    """
    resolved, err = _resolve_path(path)
    if err:
        return err

    encoded = content.encode("utf-8")
    if len(encoded) > _MAX_WRITE_BYTES:
        return (
            f"Error: content too large ({len(encoded):,} bytes). "
            f"Maximum allowed write size is {_MAX_WRITE_BYTES:,} bytes (10 MiB)."
        )

    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_bytes(encoded)
    except Exception as e:
        return f"Error writing file: {e}"

    return f"File written successfully: {resolved}"
