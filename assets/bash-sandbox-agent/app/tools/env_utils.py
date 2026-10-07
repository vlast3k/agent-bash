"""Shared environment-variable utilities for sandbox tool execution.

All subprocess-executing tools import _safe_env() from this module so that
the credential blocklist is maintained in a single place.
"""
import os

# Prefixes (and exact names) that must NOT be forwarded to subprocesses.
# Covers: AI Core tokens, SAP/BTP service credentials, MCP gateway secrets,
# Python module-path injection, dynamic-linker injection, and Git config
# overrides that could redirect git operations to attacker-controlled binaries.
_BLOCKED_ENV_PREFIXES: tuple[str, ...] = (
    "AICORE_",          # SAP AI Core credentials
    "SAP_",             # SAP BTP service bindings
    "MCP_",             # MCP gateway secrets
    "VCAP_",            # Cloud Foundry / BTP runtime bindings
    "CF_",              # Cloud Foundry internals
    "XSUAA_",           # XSUAA OAuth tokens
    "PYTHONPATH",       # prevents importing the agent's own modules
    "LD_PRELOAD",       # prevents dynamic linker injection
    "LD_LIBRARY_PATH",  # prevents library hijacking
    "GIT_SSH",          # git SSH command override
    "GIT_PROXY",        # git proxy command override
    "GIT_EXEC_PATH",    # git executable path override
    "GIT_ASKPASS",      # git credential helper override
    "GIT_SSH_COMMAND",  # explicit SSH command override (subset of GIT_SSH)
    "GIT_CONFIG",       # git config file override
)


def _safe_env() -> dict[str, str]:
    """Return a filtered copy of os.environ with sensitive variables removed.

    Uses prefix-matching for namespaced secrets and exact-name matching for
    single-name variables (e.g. PYTHONPATH) that don't carry a trailing '_'.
    """
    return {
        k: v
        for k, v in os.environ.items()
        if not any(k.startswith(p) or k == p for p in _BLOCKED_ENV_PREFIXES)
    }


def _parse_timeout(env_var: str, default: int) -> int:
    """Parse a timeout from an environment variable, falling back to *default*
    on missing or non-integer values (never raises)."""
    raw = os.environ.get(env_var, "")
    if not raw:
        return default
    try:
        value = int(raw)
        return value if value > 0 else default
    except ValueError:
        import logging
        logging.getLogger(__name__).warning(
            "Invalid value for %s=%r — using default %d seconds", env_var, raw, default
        )
        return default
