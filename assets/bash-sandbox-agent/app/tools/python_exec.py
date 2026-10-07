"""Python script/snippet execution tool — runs code in a subprocess inside the sandbox.

Security model
--------------
* Code runs in a *fresh* subprocess with a sanitised environment (no PYTHONPATH,
  no SAP_* secrets, no AI Core tokens).  The subprocess cannot reach in-process
  credentials held by the agent.
* The working directory is set to SANDBOX_WORKDIR.  Relative file operations stay
  inside the sandbox.  Absolute paths are not blocked here (that is enforced by
  file_read/file_write), but the subprocess cannot access the agent's own module
  tree because PYTHONPATH is stripped.
* A configurable wall-clock timeout terminates runaway scripts.
* Output is size-capped before reaching the LLM.
"""
import logging
import os
import subprocess
import sys
from langchain_core.tools import tool
from tools.sanitiser import sanitise
from tools.env_utils import _safe_env, _parse_timeout

log = logging.getLogger(__name__)

_MAX_OUTPUT = 8000


@tool
def python_exec(code: str) -> str:
    """Execute a Python script or snippet in the sandbox and return the output.

    The subprocess runs with a sanitised environment — SAP, AI Core, and MCP
    credentials are not forwarded, so code cannot steal in-process secrets.

    Args:
        code: Python code to execute (script or snippet).

    Returns:
        Combined stdout and stderr from the Python execution.
    """
    timeout = _parse_timeout("PYTHON_EXEC_TIMEOUT", 60)
    workdir = os.environ.get("SANDBOX_WORKDIR", "/tmp/agent-sandbox")
    os.makedirs(workdir, exist_ok=True)

    log.info("python_exec: executing snippet (len=%d, timeout=%ds)", len(code), timeout)

    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
            env=_safe_env(),   # ← sanitised env, not the full process env
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        log.warning("python_exec: timed out after %ds", timeout)  # noqa: G004
        return f"Error: Python execution timed out after {timeout} seconds."
    except Exception as e:
        return f"Error executing Python code: {e}"

    output = sanitise(output)
    if len(output) > _MAX_OUTPUT:
        output = output[:_MAX_OUTPUT] + f"\n[Output truncated at {_MAX_OUTPUT} characters]"
    return output or "(no output)"
