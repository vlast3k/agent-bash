# Multi-Source AI Agent with Bash Sandbox Tools

Autonomous Python AI agent that aggregates data from external MCP servers and executes local bash tools inside the agent's sandbox.

## Business challenge

Developers and engineers need an AI agent that can:
1. Connect to one or more external MCP servers (generic, configurable) and pull data from them.
2. Execute local bash tools — shell commands, Python scripts, file I/O, Git operations, and build/test commands — directly inside the agent's sandbox.
3. Combine the results of both external MCP calls and local tool executions to produce analysis, reports, or automated actions.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Bash command execution capability | Not available | Agent reliably executes shell, Python, file, Git, and build/test commands in sandbox | — | Developer productivity / data analysis automation | user |

## Key Milestones

1. **Agent initialised** — agent starts successfully and loads its configuration (LLM, MCP server endpoints, sandbox settings).
2. **External MCP servers connected** — agent establishes connections to all configured external MCP servers and lists their available tools.
3. **Local bash tools exposed** — agent registers shell, Python execution, file I/O, Git, and build/test commands as callable tools.
4. **Data aggregation working** — agent can invoke both external MCP tools and local bash tools within a single reasoning turn and combine their outputs.
5. **End-to-end response delivered** — agent produces a coherent analysis or action result to the user, drawing on data from all connected sources.

## Business Architecture (RBA)

### End-to-End Process

Governance → Manage Information Technology (generic)

### Process Hierarchy

```
Governance (E2E)
└── Manage Information Technology (Phase)
    └── Develop or acquire IT services (BPS-457)
        └── Acquire IT infrastructure and solutions
```

### Summary

Building a developer-facing AI agent with external MCP connectivity and local sandbox tool access maps to the "Develop or acquire IT services" sub-process within the Governance E2E. This is a custom development effort — no standard SAP product covers this capability out of the box.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
| ---------------------- | ----------------------- | ---------- | ----------------- | ------------------ | ------------------ | ------------------- | ---- | ------------------- |
| Connect to external MCP servers dynamically | None | — | — | — | — | — | Yes | Generic/configurable MCP server support; specific servers to be defined at deployment time |
| Execute shell commands in sandbox | None | — | — | — | — | — | Yes | Custom bash tool implementation inside agent sandbox |
| Execute Python scripts in sandbox | None | — | — | — | — | — | Yes | subprocess or exec-based tool inside agent |
| File read/write operations | None | — | — | — | — | — | Yes | File system tool exposed as MCP-compatible tool |
| Git operations in sandbox | None | — | — | — | — | — | Yes | Git CLI tool wrapped as agent tool |
| Build & test command execution | None | — | — | — | — | — | Yes | npm, pip, pytest etc. wrapped as agent tools |
| Aggregate results across tools | None | — | — | — | — | — | Yes | Agent reasoning layer combines MCP and bash outputs |

### Key findings

- No standard SAP product covers this use case; a fully custom Python agent is required.
- The agent will use the A2A protocol and connect to external MCP servers via the standard MCP client interface.
- Local bash tools will be implemented as Python functions registered with the agent's tool registry, running inside the agent's sandbox container.
- Security boundaries must be enforced: sandbox isolation, command allowlisting, and output sanitisation are critical design concerns.
- The solution is generic by design — specific external MCP server endpoints are injected at deployment/configuration time, making the agent reusable across projects.
- SAP AI Core can serve as the LLM runtime backend if deployment to SAP BTP is required.

## Recommendations

### Python AI Agent with External MCP + Local Bash Tools

#### Executive Summary

Pro-code Python agent connecting external MCPs and exposing bash tools in sandbox.

#### Recommended Solution

A pro-code Python AI agent built on the A2A protocol with two categories of tools:

1. **External MCP tools** — the agent acts as an MCP client, connecting to one or more externally configured MCP servers (e.g., SAP S/4HANA MCP, custom MCP servers) and exposing their tools to the LLM reasoning loop.
2. **Local bash tools** — a set of Python-wrapped tools that execute shell commands, Python scripts, file operations, Git commands, and build/test commands inside the agent's sandboxed container environment.

The agent uses an LLM (e.g., via SAP AI Core or a configured model) to reason over user requests, select the appropriate tools, invoke them, and synthesise results into a response.

#### Problem Statement

Developers need a single conversational interface to query data from multiple SAP or third-party MCP servers and perform local file/code operations — without switching between tools or writing integration scripts manually.

#### Affected User Roles

- Developers / engineers
- Data analysts (secondary)

#### Important factors

##### Full tool composability
The agent can chain external MCP calls and local bash operations within a single reasoning turn, enabling complex multi-step workflows driven by natural language.

##### Generic MCP client design
External MCP server endpoints are injected via configuration, making the agent reusable without code changes when new data sources are added.

##### Sandbox isolation
Local bash tools run inside the agent's container sandbox. Proper isolation prevents unintended side effects and keeps the execution environment reproducible.

#### Potential risks

##### Security surface of bash execution
Unrestricted bash access inside the sandbox is a significant security risk. Mitigation: implement an allowlist of permitted commands and sanitise all outputs before returning them to the LLM.

##### MCP server availability
The agent's usefulness depends on the uptime of external MCP servers. Circuit-breaker patterns and graceful degradation should be implemented.

#### Recommended solution category

AI Agent

#### Intent fit
95%
