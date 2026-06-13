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

from unittest.mock import AsyncMock, Mock, patch

import pytest
from langchain_core.runnables import RunnableLambda

from agent import MyAgent
from agent.myagent import graph_factory, prompt_template


class TestMyAgentLangGraph:
    @pytest.fixture
    def agent(self) -> MyAgent:
        mock_llm = Mock()
        return MyAgent(llm=mock_llm, verbose=True)

    def test_myagent_is_langgraph_agent_subclass(self):
        """Test that MyAgent inherits from LangGraphAgent."""
        from datarobot_genai.langgraph.agent import LangGraphAgent

        assert issubclass(MyAgent, LangGraphAgent)

    def test_init_with_llm(self):
        """Test initialization with an LLM instance."""
        mock_llm = Mock()
        agent = MyAgent(llm=mock_llm, verbose=True)
        assert agent.llm == mock_llm
        assert agent.verbose is True

    def test_prompt_template_is_runnable(self):
        """Test that prompt_template is a RunnableLambda (flexible input handler)."""
        assert isinstance(prompt_template, RunnableLambda)

    def test_prompt_template_handles_dict_input(self):
        """Test that prompt_template handles dict input with user_prompt_content."""
        result = prompt_template.invoke({"user_prompt_content": "hello world"})
        assert len(result.messages) == 1
        assert result.messages[0].content == "hello world"

    def test_prompt_template_handles_string_input(self):
        """Test that prompt_template handles plain string input."""
        result = prompt_template.invoke("hello world")
        assert len(result.messages) == 1
        assert result.messages[0].content == "hello world"

    def test_graph_factory_creates_multi_agent_nodes(self):
        """Test that graph_factory creates a graph with all expected agent nodes."""
        from langchain_core.tools import tool

        @tool
        def dummy_tool(x: str) -> str:
            """A dummy tool."""
            return x

        mock_llm = Mock()
        mock_llm.bind_tools = Mock(return_value=mock_llm)
        graph = graph_factory(mock_llm, [dummy_tool], verbose=False)
        assert graph is not None
        assert "main_agent" in graph.nodes
        assert "evaluator_agent" in graph.nodes
        assert "knowledge_base_agent" in graph.nodes
        assert "scheduled_job_agent" in graph.nodes
        assert "finalizer" in graph.nodes

    def test_graph_factory_passes_llm_and_tools(self):
        """Test that graph_factory creates the graph without error given LLM and tools."""
        from langchain_core.tools import tool

        @tool
        def dummy_tool(x: str) -> str:
            """A dummy tool."""
            return x

        mock_llm = Mock()
        mock_llm.bind_tools = Mock(return_value=mock_llm)
        graph = graph_factory(mock_llm, [dummy_tool], verbose=True)
        assert graph is not None

    def test_workflow_property_uses_graph_factory(self, agent):
        """Test that the agent's workflow property produces a graph with expected nodes."""
        workflow = agent.workflow
        assert workflow is not None
        assert "main_agent" in workflow.nodes
        assert "evaluator_agent" in workflow.nodes
        assert "knowledge_base_agent" in workflow.nodes
        assert "scheduled_job_agent" in workflow.nodes
        assert "finalizer" in workflow.nodes

    @pytest.mark.parametrize(
        "model_value, expected_model_name",
        [
            ("unknown", None),
            ("gpt-4", "gpt-4"),
            ("datarobot-deployed-llm", "datarobot-deployed-llm"),
            (None, None),
        ],
    )
    @patch("agent.myagent.get_llm", return_value=Mock())
    @patch("agent.myagent.agent_chat_completion_wrapper", new_callable=AsyncMock)
    @patch("agent.myagent.mcp_tools_context")
    def test_custompy_adaptor_filters_placeholder_models(
        self,
        mock_mcp_ctx,
        mock_wrapper,
        mock_get_llm,
        model_value,
        expected_model_name,
    ):
        from agent.myagent import custompy_adaptor

        completion_create_params = {
            "model": model_value,
            "messages": [{"role": "user", "content": "hi"}],
        }
        import asyncio

        asyncio.get_event_loop().run_until_complete(
            custompy_adaptor(completion_create_params)
        )
        mock_get_llm.assert_called_once()
        assert mock_get_llm.call_args[1]["model_name"] == expected_model_name
