# Copyright 2026 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import logging
import re
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, cast

import litellm
from datarobot_genai.core.agents import InvokeReturn, make_system_prompt
from datarobot_genai.core.agents.base import UsageMetrics
from datarobot_genai.core.chat import agent_chat_completion_wrapper
from datarobot_genai.core.mcp import MCPConfig
from datarobot_genai.langgraph.agent import datarobot_agent_class_from_langgraph
from datarobot_genai.langgraph.llm import get_llm
from datarobot_genai.langgraph.mcp import mcp_tools_context
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from openai.types.chat import CompletionCreateParams

if TYPE_CHECKING:
    from ragas import MultiTurnSample

from agent.config import Config
from agent.tools import make_tavily_search_tool, store_to_knowledge_base

log = logging.getLogger(__name__)

litellm.modify_params = True

_PLACEHOLDER_MODELS = frozenset({"unknown"})

KNOWLEDGE_BASE_TRIGGER = "Store this:"


class _ScheduledJobState(MessagesState):
    search_calls: int


def _load_agent_soul(agent_name: str, config: Config) -> str:
    """Load the SOUL.md for a given agent subfolder, substitute config values, and prepend today's date."""
    soul_path = Path(__file__).parent / "agents" / agent_name / "SOUL.md"
    if not soul_path.exists():
        raise FileNotFoundError(f"SOUL.md not found at {soul_path}")
    content = soul_path.read_text().format(
        owner_name=config.owner_name,
        bot_name=config.bot_name,
        slack_owner_user_id=config.slack_owner_user_id,
    )
    return f"Today's date is {date.today().isoformat()}.\n\n{content}"


def graph_factory(
    llm: BaseChatModel, tools: list[BaseTool], verbose: bool = False
) -> StateGraph[MessagesState]:
    """Build the multi-agent routing graph.

    Args:
        llm: The chat model injected by the runtime.
        tools: MCP tools provided by the runtime.
        verbose: Enable verbose logging in agent nodes.
    """
    config = Config()

    # ------------------------------------------------------------------ main --
    main_soul = _load_agent_soul("main", config)
    main_system_prompt = (
        "You are responding as the person described below. Embody their personality, "
        "technical preferences, and communication style.\n\n"
        "ALWAYS use Slack markdown formatting:\n"
        "- Use *bold* for emphasis (not **bold**)\n"
        "- Use _italic_ for italic text (not *italic*)\n"
        "- Use `code` for inline code\n"
        "- Use ```language\\ncode\\n``` for code blocks\n"
        "- Use > for quotes\n"
        "- Use • or - for bullet lists\n"
        "- Use 1. 2. 3. for numbered lists\n\n"
        "IMPORTANT - Slack does NOT support:\n"
        "- NO headings like # or ## or ### - these do not work in Slack\n"
        "- For section titles, use *Bold Text* on its own line instead\n"
        "- For separation, use blank lines or --- dividers\n\n"
        f"PERSONA DEFINITION:\n{main_soul}\n\n"
        "Respond naturally as this person would, using their voice and perspective."
    )
    main_agent = create_agent(
        llm,
        tools=[],
        system_prompt=make_system_prompt(main_system_prompt),
        name="Main Agent",
        debug=verbose,
    )

    # -------------------------------------------------------------- evaluator --
    evaluator_agent = create_agent(
        llm,
        tools=[],
        system_prompt=make_system_prompt(_load_agent_soul("evaluator", config)),
        name="Evaluator Agent",
        debug=verbose,
    )

    # --------------------------------------------------------- knowledge base --
    knowledge_base_agent = create_agent(
        llm,
        tools=[store_to_knowledge_base],
        system_prompt=make_system_prompt(_load_agent_soul("knowledge_base", config)),
        name="Knowledge Base Agent",
        debug=verbose,
    )

    # --------------------------------------------------------- scheduled jobs --
    MAX_SEARCH_CALLS = 4
    scheduled_soul = _load_agent_soul("scheduled_job", config)
    tavily_tools = [make_tavily_search_tool()] if config.tavily_api_key else []
    if not config.tavily_api_key:
        log.warning(
            "graph_factory: TAVILY_API_KEY not configured — tavily search disabled"
        )

    scheduled_job_tools = [*tavily_tools, *tools]
    tool_node = ToolNode(scheduled_job_tools)
    llm_with_tools = llm.bind_tools(scheduled_job_tools)

    async def call_model(state: _ScheduledJobState) -> dict[str, Any]:
        search_calls = state.get("search_calls", 0)
        log.info("scheduled_job call_model: search_calls=%d", search_calls)
        messages = [SystemMessage(content=scheduled_soul)] + list(state["messages"])
        response = await llm_with_tools.ainvoke(messages)
        tool_calls = getattr(response, "tool_calls", [])
        log.info(
            "scheduled_job call_model: response type=%s tool_calls=%s",
            type(response).__name__,
            [tc.get("name") for tc in tool_calls],
        )
        return {"messages": [response]}

    async def call_tools(state: _ScheduledJobState) -> dict[str, Any]:
        last = state["messages"][-1]
        tool_calls = getattr(last, "tool_calls", [])
        log.info(
            "scheduled_job call_tools: invoking %d tool(s): %s",
            len(tool_calls),
            [tc.get("name") for tc in tool_calls],
        )
        result = await tool_node.ainvoke({"messages": state["messages"]})
        tavily_calls = sum(
            1 for tc in tool_calls if tc.get("name") == "tavily_search_results_json"
        )
        current = state.get("search_calls", 0)
        log.info(
            "scheduled_job call_tools: tavily_calls=%d total=%d",
            tavily_calls,
            current + tavily_calls,
        )
        return {
            "messages": result["messages"],
            "search_calls": current + tavily_calls,
        }

    async def summarize(state: _ScheduledJobState) -> dict[str, Any]:
        last = cast(AIMessage, state["messages"][-1])
        log.info(
            "scheduled_job summarize: budget exhausted (search_calls=%d), synthesizing",
            state.get("search_calls", 0),
        )
        stop_msgs = [
            ToolMessage(
                content="Search budget exhausted. Synthesize from results already gathered.",
                tool_call_id=tc["id"],
            )
            for tc in last.tool_calls
        ]
        messages = (
            [SystemMessage(content=scheduled_soul)]
            + list(state["messages"])
            + stop_msgs
        )
        return {"messages": stop_msgs + [await llm_with_tools.ainvoke(messages)]}

    def should_continue(state: _ScheduledJobState) -> str:
        last = cast(AIMessage, state["messages"][-1])
        tool_calls = getattr(last, "tool_calls", [])
        search_calls = state.get("search_calls", 0)
        if not tool_calls:
            log.info("scheduled_job should_continue: no tool calls -> END")
            return END
        if search_calls >= MAX_SEARCH_CALLS:
            log.info(
                "scheduled_job should_continue: search_calls=%d >= MAX=%d -> summarize",
                search_calls,
                MAX_SEARCH_CALLS,
            )
            return "summarize"
        log.info(
            "scheduled_job should_continue: tool_calls=%s -> tools",
            [tc.get("name") for tc in tool_calls],
        )
        return "tools"

    scheduled_subgraph = StateGraph(_ScheduledJobState)
    scheduled_subgraph.add_node("agent", call_model)
    scheduled_subgraph.add_node("tools", call_tools)
    scheduled_subgraph.add_node("summarize", summarize)
    scheduled_subgraph.add_edge(START, "agent")
    scheduled_subgraph.add_conditional_edges(
        "agent", should_continue, ["tools", "summarize", END]
    )
    scheduled_subgraph.add_edge("tools", "agent")
    scheduled_subgraph.add_edge("summarize", END)
    scheduled_job_compiled = scheduled_subgraph.compile()

    # ---------------------------------------------------------------- finalizer --
    finalizer_soul = _load_agent_soul("finalizer", config)

    async def finalizer_node(state: MessagesState) -> dict[str, Any]:
        last_ai = next(
            (
                m
                for m in reversed(state["messages"])
                if isinstance(m, AIMessage) and m.content
            ),
            None,
        )
        if last_ai is None:
            log.warning("finalizer: no AIMessage with content found")
            return {"messages": [AIMessage(content="")]}
        messages = [
            SystemMessage(content=finalizer_soul),
            HumanMessage(content=str(last_ai.content)),
        ]
        response = await llm.ainvoke(messages)
        return {"messages": [response]}

    # --------------------------------------------------- scheduled job wrapper --
    async def run_scheduled_job(state: MessagesState) -> dict[str, Any]:
        """Run the scheduled job subgraph and isolate its final message."""
        try:
            result = await scheduled_job_compiled.ainvoke(
                cast(_ScheduledJobState, state)
            )
        except Exception as exc:
            log.exception("run_scheduled_job: unhandled exception: %s", exc)
            return {
                "messages": [
                    AIMessage(
                        content=f"Scheduled job failed: {type(exc).__name__}: {exc}"
                    )
                ]
            }
        final_msg = next(
            (
                m
                for m in reversed(result["messages"])
                if isinstance(m, AIMessage) and not getattr(m, "tool_calls", None)
            ),
            None,
        )
        if final_msg is None:
            log.warning(
                "run_scheduled_job: no clean AIMessage found, using last message"
            )
            final_msg = result["messages"][-1]
        log.info(
            "run_scheduled_job: final message content_len=%d",
            len(str(final_msg.content)),
        )
        return {"messages": [final_msg]}

    # ----------------------------------------------------------- content router --
    def route_by_content(state: MessagesState) -> str:
        last_msg = state["messages"][-1]
        content = str(getattr(last_msg, "content", ""))
        log.info(
            "route_by_content: msg_type=%s content_len=%d content=%r",
            type(last_msg).__name__,
            len(content),
            content[:200],
        )
        if not content:
            log.info("route_by_content: empty content -> main_agent")
            return "main_agent"
        if KNOWLEDGE_BASE_TRIGGER in content:
            log.info(
                "route_by_content: knowledge base trigger detected -> knowledge_base_agent"
            )
            return "knowledge_base_agent"
        try:
            if content.strip().startswith("{"):
                data = json.loads(content)
            else:
                match = re.search(r"({.*})", content, re.DOTALL)
                data = json.loads(match.group(1)) if match else {}

            if isinstance(data, dict) and data.get("task_type") == "mention_evaluation":
                log.info(
                    "route_by_content: task_type=mention_evaluation -> evaluator_agent"
                )
                return "evaluator_agent"
            if isinstance(data, dict) and data.get("task_type") == "scheduled_job":
                log.info(
                    "route_by_content: task_type=scheduled_job -> scheduled_job_agent"
                )
                return "scheduled_job_agent"
        except Exception:
            log.exception(
                "route_by_content: failed to parse content, defaulting to main_agent"
            )
        return "main_agent"

    # ------------------------------------------------------------- wire graph --
    langgraph_workflow: StateGraph[MessagesState] = StateGraph(MessagesState)
    langgraph_workflow.add_node("main_agent", main_agent)
    langgraph_workflow.add_node("evaluator_agent", evaluator_agent)
    langgraph_workflow.add_node("knowledge_base_agent", knowledge_base_agent)
    langgraph_workflow.add_node("scheduled_job_agent", run_scheduled_job)
    langgraph_workflow.add_node("finalizer", finalizer_node)

    langgraph_workflow.add_conditional_edges(START, route_by_content)
    langgraph_workflow.add_edge("main_agent", "finalizer")
    langgraph_workflow.add_edge("scheduled_job_agent", "finalizer")
    langgraph_workflow.add_edge("evaluator_agent", END)
    langgraph_workflow.add_edge("knowledge_base_agent", "finalizer")
    langgraph_workflow.add_edge("finalizer", END)
    return langgraph_workflow


def _build_prompt_template() -> RunnableLambda[Any, ChatPromptValue]:
    def flexible_prompt(inputs: Any) -> ChatPromptValue:
        log.info(
            "flexible_prompt: inputs type=%s value=%r",
            type(inputs).__name__,
            str(inputs)[:300],
        )
        if isinstance(inputs, dict) and "user_prompt_content" in inputs:
            content = str(inputs["user_prompt_content"])
        elif isinstance(inputs, str):
            content = inputs
        else:
            content = json.dumps(inputs)
        log.info("flexible_prompt: content=%r", content[:200])
        return ChatPromptValue(messages=[HumanMessage(content=content)])

    return RunnableLambda(flexible_prompt)


prompt_template: ChatPromptTemplate = _build_prompt_template()  # type: ignore[assignment]

MyAgent = datarobot_agent_class_from_langgraph(graph_factory, prompt_template)


async def custompy_adaptor(
    completion_create_params: CompletionCreateParams,
) -> InvokeReturn | tuple[str, Optional["MultiTurnSample"], UsageMetrics]:
    forwarded_headers = completion_create_params.get("forwarded_headers", {})
    authorization_context = completion_create_params.get("authorization_context", {})
    mcp_config = MCPConfig(
        forwarded_headers=forwarded_headers,
        authorization_context=authorization_context,
    )
    mcp_tools_factory = lambda: mcp_tools_context(mcp_config)  # noqa: E731
    model_name = completion_create_params.get("model")
    agent = MyAgent(
        llm=get_llm(
            model_name=model_name if model_name not in _PLACEHOLDER_MODELS else None
        ),
        verbose=completion_create_params.get("verbose", True),  # type: ignore[arg-type]
        timeout=completion_create_params.get("timeout", 90),  # type: ignore[arg-type]
        forwarded_headers=forwarded_headers,  # type: ignore[arg-type]
    )
    return await agent_chat_completion_wrapper(
        agent, completion_create_params, mcp_tools_factory
    )
