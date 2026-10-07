"""Build and test command execution tool — runs allowlisted build/test commands in the sandbox."""
import logging
import os
import subprocess
import shlex
from langchain_core.tools import tool
from tools.sanitiser import sanitise
from tools.env_utils import _safe_env, _parse_timeout

log = logging.getLogger(__name__)

_DEFAULT_ALLOWLIST = "npm,pip,pip3,pytest,yarn,mvn,gradle,make,python,python3"
_MAX_OUTPUT = 10000


def _get_allowlist() -> set[str]:
    raw = os.environ.get("BUILD_TEST_ALLOWLIST", _DEFAULT_ALLOWLIST)
    return {cmd.strip() for cmd in raw.split(",") if cmd.strip()}


def _effective_command_token(tokens: list[str]) -> str:
    """Return the logical command identifier for allowlist checking.

    Handles the 'python -m <module>' pattern: the effective command is the
    module name (e.g. 'pytest' for 'python -m pytest'), because that is what
    operators configure in the allowlist — not the interpreter name.

    Previous implementation set effective_token = first_token unconditionally
    (dead code), which meant 'python -m curl' was allowed whenever 'python'
    was on the allowlist.  This implementation gates on the module name instead.
    """
    first = tokens[0]
    if (
        first in {"python", "python3"}
        and len(tokens) > 2
        and tokens[1] == "-m"
    ):
        return tokens[2]   # the module name is the effective command
    return first


@tool
def build_test(command: str) -> str:
    """Execute an allowlisted build or test command in the sandbox.
    Returns the exit code, stdout, and stderr. Highlights failures (non-zero exit codes).

    Args:
        command: Build or test command (e.g. 'pytest tests/', 'npm test',
                 'python -m pytest', 'pip install requests').

    Returns:
        Exit code and combined output from the command.
    """
    allowlist = _get_allowlist()
    timeout = _parse_timeout("BUILD_TEST_TIMEOUT", 120)
    workdir = os.environ.get("SANDBOX_WORKDIR", "/tmp/agent-sandbox")
    os.makedirs(workdir, exist_ok=True)

    try:
        tokens = shlex.split(command)
    except ValueError as e:
        return f"Error parsing command: {e}"

    if not tokens:
        return "Error: empty command."

    effective_token = _effective_command_token(tokens)

    if effective_token not in allowlist:
        log.warning("BLOCKED build_test — command not on allowlist: '%s'", effective_token)
        return (
            f"Command '{effective_token}' is not allowed. "
            f"Permitted commands: {', '.join(sorted(allowlist))}"
        )

    log.info("build_test: executing '%s' in %s (timeout=%ds)", command, workdir, timeout)

    try:
        result = subprocess.run(
            tokens,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=workdir,
            env=_safe_env(),   # strips SAP/AI Core secrets; prevents malicious package scripts reading them
        )
        output = result.stdout + result.stderr
        status = "SUCCESS" if result.returncode == 0 else f"FAILED (exit code {result.returncode})"
    except subprocess.TimeoutExpired:
        log.warning("build_test: timed out after %ds: '%s'", timeout, command)
        return f"Error: command timed out after {timeout} seconds."
    except Exception as e:
        return f"Error executing command: {e}"

    output = sanitise(output)
    if len(output) > _MAX_OUTPUT:
        output = output[:_MAX_OUTPUT] + f"\n[Output truncated at {_MAX_OUTPUT} characters]"

    return f"[{status}]\n{output}" if output else f"[{status}]\n(no output)"
