"""Git operations tool — runs Git commands inside the sandbox working directory.

Subcommand classification
-------------------------
READ_ONLY — executed immediately, no confirmation needed.
WRITE     — documented as requiring prior user confirmation in the system prompt.

Note: 'remote' is intentionally NOT in READ_ONLY because `git remote add …` and
`git remote remove …` are mutating operations.  It is placed in WRITE so the
system prompt can warn the user before it executes.
"""
import logging
import os
import subprocess
import shlex
from langchain_core.tools import tool
from tools.sanitiser import sanitise
from tools.env_utils import _safe_env

log = logging.getLogger(__name__)

_READ_ONLY_COMMANDS = {"status", "diff", "log", "show", "branch", "ls-files"}
_WRITE_COMMANDS = {
    "commit", "add", "push", "reset", "checkout", "merge",
    "rebase", "tag", "remote", "fetch", "stash",
}
_MAX_OUTPUT = 8000


@tool
def git_tool(command: str) -> str:
    """Run a Git command in the sandbox repository.
    Read-only commands (status, diff, log, show, branch, ls-files) execute immediately.
    Write commands (commit, add, push, reset, remote, etc.) require prior user confirmation.

    Args:
        command: Git subcommand and arguments (e.g. 'status', 'log --oneline -10', 'diff HEAD').

    Returns:
        Combined stdout and stderr from the Git command.
    """
    workdir = os.environ.get("SANDBOX_WORKDIR", "/tmp/agent-sandbox")
    os.makedirs(workdir, exist_ok=True)

    try:
        tokens = shlex.split(command)
    except ValueError as e:
        return f"Error parsing git command: {e}"

    if not tokens:
        return "Error: empty git command."

    subcommand = tokens[0]
    if subcommand not in _READ_ONLY_COMMANDS and subcommand not in _WRITE_COMMANDS:
        log.warning("BLOCKED git_tool — unsupported subcommand: '%s'", subcommand)
        return (
            f"Git subcommand '{subcommand}' is not supported. "
            f"Supported read-only: {', '.join(sorted(_READ_ONLY_COMMANDS))}. "
            f"Supported write (require confirmation): {', '.join(sorted(_WRITE_COMMANDS))}."
        )

    log.info("git_tool: executing 'git %s' in %s", command, workdir)

    try:
        result = subprocess.run(
            ["git"] + tokens,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=workdir,
            env=_safe_env(),   # strips SAP/AI Core secrets; prevents git hook exfiltration
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "Error: git command timed out after 30 seconds."
    except Exception as e:
        return f"Error executing git command: {e}"

    output = sanitise(output)
    if len(output) > _MAX_OUTPUT:
        output = output[:_MAX_OUTPUT] + f"\n[Output truncated at {_MAX_OUTPUT} characters]"
    return output or "(no output)"
