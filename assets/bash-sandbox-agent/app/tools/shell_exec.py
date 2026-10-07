"""Shell command execution tool — runs allowlisted bash commands in the sandbox."""
import logging
import os
import re
import subprocess
import shlex
from pathlib import Path
from langchain_core.tools import tool
from tools.sanitiser import sanitise
from tools.env_utils import _safe_env

log = logging.getLogger(__name__)

_DEFAULT_ALLOWLIST = "ls,grep,find,cat,echo,pwd,whoami,df,du,env,head,tail,wc,sort,uniq,diff,date,uname"
_MAX_OUTPUT = 8000

# Argument patterns that are dangerous regardless of the binary being called.
# Note: '>' and '<' (redirection) are NOT shell meta-characters when subprocess
# is called with a list (no shell=True) — they are passed as literal arguments.
# They are included here anyway to prevent confusion and edge cases where a
# future caller might accidentally enable shell=True.
_DANGEROUS_ARG_PATTERNS = [
    re.compile(r"[;&|`$\\<>]"),         # shell meta-characters / injection / redirection
    re.compile(r"-exec\b"),             # find -exec arbitrary command
    re.compile(r"--exec\b"),
]


def _get_allowlist() -> set[str]:
    raw = os.environ.get("SHELL_ALLOWLIST", _DEFAULT_ALLOWLIST)
    return {cmd.strip() for cmd in raw.split(",") if cmd.strip()}


def _arg_is_safe(arg: str, workdir: str) -> tuple[bool, str]:
    """Return (safe, reason). Rejects absolute paths outside the sandbox and
    dangerous shell meta-characters in arguments."""
    for pat in _DANGEROUS_ARG_PATTERNS:
        if pat.search(arg):
            return False, f"Argument contains forbidden pattern: '{arg}'"
    # Reject absolute paths that escape the sandbox
    if arg.startswith("/"):
        try:
            resolved = Path(arg).resolve()
            sandbox = Path(workdir).resolve()
            if not (resolved == sandbox or resolved.is_relative_to(sandbox)):
                return False, f"Absolute path '{arg}' resolves outside the sandbox."
        except Exception:
            return False, f"Could not resolve path argument: '{arg}'"
    return True, ""


@tool
def shell_exec(command: str) -> str:
    """Execute an allowlisted shell command in the sandbox and return its output.

    Args:
        command: The shell command to execute (e.g. 'ls -la', 'grep error app.log').
                 Absolute paths outside the sandbox and shell meta-characters are rejected.

    Returns:
        Combined stdout and stderr from the command execution.
    """
    allowlist = _get_allowlist()
    try:
        tokens = shlex.split(command)
    except ValueError as e:
        return f"Error parsing command: {e}"

    if not tokens:
        return "Error: empty command."

    first_token = tokens[0]
    if first_token not in allowlist:
        log.warning("BLOCKED shell_exec — command not on allowlist: '%s'", first_token)
        return (
            f"Command '{first_token}' is not allowed. "
            f"Permitted commands: {', '.join(sorted(allowlist))}"
        )

    workdir = os.environ.get("SANDBOX_WORKDIR", "/tmp/agent-sandbox")
    os.makedirs(workdir, exist_ok=True)

    # Validate arguments
    for arg in tokens[1:]:
        safe, reason = _arg_is_safe(arg, workdir)
        if not safe:
            log.warning("BLOCKED shell_exec argument: %s", reason)
            return f"Argument rejected: {reason}"

    try:
        result = subprocess.run(
            tokens,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=workdir,
            env=_safe_env(),   # filtered env: strips SAP/AI Core secrets; keeps PATH/LANG/HOME
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 30 seconds."
    except Exception as e:
        return f"Error executing command: {e}"

    output = sanitise(output)
    if len(output) > _MAX_OUTPUT:
        output = output[:_MAX_OUTPUT] + f"\n[Output truncated at {_MAX_OUTPUT} characters]"
    return output or "(no output)"
