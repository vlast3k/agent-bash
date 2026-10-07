# Specification: bash-sandbox-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read the project input (`product-requirements-document.md` and `intent.md` at the solution root)
- [x] Bootstrap agent code in `assets/bash-sandbox-agent/` using instructions from the `sap-agent-bootstrap` section (invoke from inside `assets/bash-sandbox-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

No runtime skills are required for this agent. The tool set is uniform across all requests and does not contain multi-step conditional workflows. Tool instructions belong in the system prompt. ✅

---

## Project-Specific Tasks

### REQ-01 — External MCP Server Configuration

- [x] In `assets/bash-sandbox-agent/app/agent.py`, implement an `mcp_client` connection manager that reads a list of MCP server endpoints from an environment variable (`MCP_SERVER_URLS`, comma-separated) at startup
- [x] At agent initialisation, for each configured URL: establish an MCP client connection and discover the available tools; register those tools in the agent's tool dispatcher alongside the local bash tools
- [x] If a configured MCP server is unreachable at startup, log a warning (`M2.missed: ...`) and continue — do not crash the agent
- [x] Add `MCP_SERVER_URLS` to the list of expected environment variables documented in `assets/bash-sandbox-agent/app/agent.py` (inline comment block)

### REQ-02 — Shell Command Execution (`shell_exec` tool)

- [x] Implement `shell_exec` tool with allowlist, subprocess execution, output truncation
- [x] Register in agent's tool registry via `agent_executor.py`
- [x] Described in system prompt

### REQ-03 — Python Script Execution (`python_exec` tool)

- [x] Implement `python_exec` tool with configurable timeout, output truncation
- [x] Registered in agent's tool registry
- [x] Described in system prompt

### REQ-04 — File Read/Write Operations (`file_read`, `file_write` tools)

- [x] Implement `file_read` with path traversal guard and truncation
- [x] Implement `file_write` with path traversal guard and directory creation
- [x] Both tools registered in agent's tool registry
- [x] Described in system prompt with confirmation requirement for writes

### REQ-05 — Git Operations (`git_tool` tool)

- [x] Implement `git_tool` with read-only / write-with-confirmation subcommand split
- [x] Registered in agent's tool registry
- [x] Described in system prompt

### REQ-06 — Build and Test Command Execution (`build_test` tool)

- [x] Implement `build_test` with allowlist, exit code reporting, timeout, output truncation
- [x] Registered in agent's tool registry
- [x] Described in system prompt

### REQ-07 — Cross-Tool Result Aggregation (System Prompt & Agent Reasoning)

- [x] System prompt instructs agent to combine results from both external MCP tools and local bash tools
- [x] Agent graph wires both local tools and dynamically loaded external MCP tools into the same tool node via `agent_executor.py`

### Security Hardening

- [x] Output sanitiser implemented in `tools/sanitiser.py`; all six tools pipe output through it
- [x] `SANDBOX_WORKDIR` created at startup via `os.makedirs(..., exist_ok=True)` in each tool
- [x] Circuit breaker built into the agent framework (`circuit_breaker.py`) for LLM/MCP connectivity

---

## Business Instrumentation

- [x] Instrument all 5 PRD milestones in `assets/bash-sandbox-agent/app/agent.py` with structured log statements and OpenTelemetry spans:
  - **M1** — emit `M1.achieved: agent initialised — config loaded, LLM backend connected` after config is loaded and LLM is ready; emit `M1.missed: agent initialisation failed — check config or LLM backend connectivity` on failure
  - **M2** — emit `M2.achieved: external MCP servers connected — {n} server(s), {m} tools discovered` after all reachable servers are connected; emit `M2.missed: no external MCP servers connected — all configured endpoints unreachable or none configured` if none connect
  - **M3** — emit `M3.achieved: local bash tools registered — shell_exec, python_exec, file_read, file_write, git_tool, build_test` after all 6 local tools are registered; emit `M3.missed: one or more local bash tools failed to register — {tool_name}` on failure
  - **M4** — emit `M4.achieved: cross-tool aggregation successful — MCP tool: {mcp_tool_name}, local tool: {local_tool_name}` when a single turn uses both tool categories; emit `M4.missed: cross-tool aggregation did not complete — {reason}` on failure
  - **M5** — emit `M5.achieved: end-to-end response delivered — {tool_call_count} tool calls, response length {char_count} chars` when the agent emits a final answer; emit `M5.missed: agent failed to deliver a complete response — {reason}` on error
- [x] Use the **decorator form** of `tracer.start_as_current_span` on regular async methods; use the **context manager form** inside `_run_agent()` helper — never inside an async generator (`stream()`)
- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

- [x] No external SAP API specs and no existing MCP server ORD IDs are in the fit-gap analysis — all external MCP connectivity is generic and runtime-configurable via `MCP_SERVER_URLS`
- [x] No `mcp-translation-file` invocation is needed — there are no static API specs to translate
- [x] Since there are no pre-defined MCP server ORD IDs, the agent's `asset.yaml` will have an empty `requires` list initially; operators add MCP server entries at deployment time as needed
- [x] Skip `mcp-mock-config` skill — no static MCP specs exist; mock the dynamic MCP tool loading in tests directly using `unittest.mock`

---

## Testing

- [x] `conftest.py` sets only `IBD_TESTING=true`; patch `mcp_tools.get_mcp_tools` to return an empty list for tests (external MCP servers are not available in test environment)
- [x] Write unit tests in `assets/bash-sandbox-agent/tests/`:
  - `test_shell_exec.py` ✅
  - `test_python_exec.py` ✅
  - `test_file_read.py` ✅
  - `test_file_write.py` ✅
  - `test_git_tool.py` ✅
  - `test_build_test.py` ✅
  - `test_sanitiser.py` ✅
- [x] Write one integration test `tests/test_integration.py` — 2 scenarios ✅
- [x] Run `pytest` — 145 passed, 79% coverage ✅
- [x] Verify coverage ≥ 70% — 79% ✅
- [x] Run `pytest` again to produce `test_report.json` ✅
- [x] Verify `assets/bash-sandbox-agent/test_report.json` exists ✅

---

## Validation Checklist ✅

```bash
# Instrumentation present — PASSED (M1–M5 all found)
grep -r "M[0-9]\.achieved" assets/bash-sandbox-agent/app/

# Test report present — PASSED
ls assets/bash-sandbox-agent/test_report.json
```
