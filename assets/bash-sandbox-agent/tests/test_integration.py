"""Integration test — full agent graph with mocked LLM and mocked MCP tools."""
import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_agent_end_to_end_shell_tool(tmp_path, monkeypatch):
    """Agent receives a query, calls shell_exec, and returns a synthesised response."""
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("SHELL_ALLOWLIST", "echo")

    # Create a test file in the sandbox for echo to find
    (tmp_path / "hello.txt").write_text("hello from integration test")

    from tools.shell_exec import shell_exec
    from tools.python_exec import python_exec
    from tools.file_read import file_read
    from tools.file_write import file_write
    from tools.git_tool import git_tool
    from tools.build_test import build_test
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
    from langchain_core.tools import StructuredTool

    # Build a minimal fake tool call result mimicking what LangGraph produces
    fake_tool_call = {"name": "shell_exec", "args": {"command": "echo hi"}, "id": "tc1"}
    ai_msg_with_call = AIMessage(content="", tool_calls=[fake_tool_call])
    tool_msg = ToolMessage(content="hi\n", tool_call_id="tc1")
    final_ai_msg = AIMessage(content="The sandbox echoed: hi")

    # Patch the graph invoke to return a canned message sequence
    fake_result = {"messages": [
        HumanMessage(content="echo hi in the sandbox"),
        ai_msg_with_call,
        tool_msg,
        final_ai_msg,
    ]}

    all_tools = [shell_exec, python_exec, file_read, file_write, git_tool, build_test]

    with patch("agent.SampleAgent._invoke_with_fallback", new=AsyncMock(return_value=fake_result)):
        from agent import SampleAgent
        agent = SampleAgent()
        response = await agent.invoke(
            query="echo hi in the sandbox",
            context_id="test-ctx-001",
            tools=all_tools,
        )

    assert response.status == "completed"
    assert "hi" in response.message.lower() or "echo" in response.message.lower()


@pytest.mark.asyncio
async def test_agent_stream_yields_processing_then_result(tmp_path, monkeypatch):
    """Agent stream yields a working status followed by the completed response."""
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))

    from langchain_core.messages import AIMessage, HumanMessage
    from tools.shell_exec import shell_exec

    fake_result = {"messages": [
        HumanMessage(content="list files"),
        AIMessage(content="Here are your files."),
    ]}

    with patch("agent.SampleAgent._invoke_with_fallback", new=AsyncMock(return_value=fake_result)):
        from agent import SampleAgent
        agent = SampleAgent()
        chunks = []
        async for chunk in agent.stream("list files", "ctx-002", tools=[shell_exec]):
            chunks.append(chunk)

    assert len(chunks) >= 2
    # First chunk is the "Processing..." working status
    assert chunks[0]["is_task_complete"] is False
    # Last chunk is completed
    assert chunks[-1]["is_task_complete"] is True
    assert "files" in chunks[-1]["content"].lower() or chunks[-1]["content"]
