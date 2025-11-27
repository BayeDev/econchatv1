"""Query Router - Intelligent orchestration using Claude.

This module handles the core AI-powered query routing and execution.
It uses Claude to:
1. Understand user intent
2. Decide which tools to call
3. Execute multi-step reasoning
4. Compose final responses
"""

import json
import uuid
from typing import Any, AsyncGenerator, Optional
from dataclasses import dataclass, field

from anthropic import Anthropic

from app.config import get_settings
from app.orchestration.tools import get_tools_for_claude, ToolName
from app.orchestration.executor import ToolExecutor
from app.visualization.selector import VisualizationSelector

settings = get_settings()


@dataclass
class QueryResult:
    """Result from processing a query."""

    message_id: str
    content: str
    data: Optional[dict] = None
    visualization: Optional[dict] = None
    sources: Optional[list[dict]] = None
    suggested_followups: Optional[list[str]] = None
    tool_calls: list[dict] = field(default_factory=list)


SYSTEM_PROMPT = """You are EconChat, an AI assistant specialized in economic data analysis for economists at multilateral development banks (World Bank, IMF, IsDB, etc.).

Your capabilities:
1. Fetch real-time economic data from World Bank and other sources
2. Search internal documents and reports
3. Analyze trends and patterns in economic indicators
4. Compare countries and benchmark performance
5. Generate insightful visualizations

When responding:
- Be precise and data-driven
- Use appropriate economic terminology
- Cite data sources
- Suggest relevant follow-up analyses
- Consider regional context (especially for African economies)

Available data includes:
- World Development Indicators (GDP, inflation, trade, etc.)
- Country income classifications and regional groupings
- Historical data from 1960 to present

For country references:
- Use ISO3 codes internally (NGA for Nigeria, KEN for Kenya, etc.)
- Recognize common names and abbreviations
- Understand regional groups (Sub-Saharan Africa, MENA, etc.)

For time periods:
- Default to last 10 years if not specified
- Understand phrases like "since 2010", "last 5 years", "recent"
- Handle specific year ranges like "2015-2023"

Always think step-by-step:
1. What is the user asking for?
2. What data/tools do I need?
3. How should I present the results?
4. What follow-up questions might be relevant?
"""


class QueryRouter:
    """Routes and processes user queries using Claude orchestration."""

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        self.tools = get_tools_for_claude()
        self.executor = ToolExecutor()
        self.viz_selector = VisualizationSelector()

    async def process(self, query: str, context: dict) -> QueryResult:
        """Process a query and return the result."""
        message_id = str(uuid.uuid4())

        if not self.client:
            # Fallback to rule-based processing if no API key
            return await self._process_fallback(query, context, message_id)

        # Build messages with context
        messages = self._build_messages(query, context)

        # Call Claude with tools
        response = self.client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.claude_max_tokens,
            system=SYSTEM_PROMPT,
            tools=self.tools,
            messages=messages,
        )

        # Process tool calls if any
        result = await self._process_response(response, context, message_id)

        return result

    async def process_stream(
        self, query: str, context: dict
    ) -> AsyncGenerator[dict, None]:
        """Process a query with streaming response."""

        if not self.client:
            # Fallback to rule-based processing
            async for event in self._stream_fallback(query, context):
                yield event
            return

        # Build messages with context
        messages = self._build_messages(query, context)

        # Stream from Claude
        with self.client.messages.stream(
            model=settings.claude_model,
            max_tokens=settings.claude_max_tokens,
            system=SYSTEM_PROMPT,
            tools=self.tools,
            messages=messages,
        ) as stream:
            current_tool = None
            accumulated_text = ""

            for event in stream:
                if event.type == "content_block_start":
                    if hasattr(event.content_block, "type"):
                        if event.content_block.type == "tool_use":
                            current_tool = {
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "input": "",
                            }
                            yield {
                                "type": "tool_call",
                                "tool": event.content_block.name,
                            }

                elif event.type == "content_block_delta":
                    if hasattr(event.delta, "text"):
                        accumulated_text += event.delta.text
                        yield {"type": "content", "content": event.delta.text}

                    elif hasattr(event.delta, "partial_json"):
                        if current_tool:
                            current_tool["input"] += event.delta.partial_json

                elif event.type == "content_block_stop":
                    if current_tool:
                        # Execute the tool
                        try:
                            tool_input = json.loads(current_tool["input"])
                            result = await self.executor.execute(
                                current_tool["name"], tool_input
                            )
                            yield {
                                "type": "tool_result",
                                "tool": current_tool["name"],
                                "data": result,
                            }

                            # Generate visualization if data was fetched
                            if current_tool["name"] == ToolName.FETCH_ECONOMIC_DATA:
                                viz_config = self.viz_selector.select(
                                    query_type="time_series",
                                    data=result,
                                )
                                yield {
                                    "type": "visualization",
                                    "config": viz_config,
                                    "data": result,
                                }

                        except Exception as e:
                            yield {
                                "type": "tool_result",
                                "tool": current_tool["name"],
                                "error": str(e),
                            }

                        current_tool = None

    def _build_messages(self, query: str, context: dict) -> list[dict]:
        """Build the message list with conversation context."""
        messages = []

        # Add recent conversation history from context
        history = context.get("history", [])
        for msg in history[-10:]:  # Last 10 messages for context
            messages.append(
                {"role": msg["role"], "content": msg["content"]}
            )

        # Add current query
        messages.append({"role": "user", "content": query})

        # Add entity context as system message if available
        entities = context.get("entities", {})
        if entities:
            context_note = self._build_context_note(entities)
            # Prepend context to user message
            messages[-1]["content"] = f"{context_note}\n\nUser query: {query}"

        return messages

    def _build_context_note(self, entities: dict) -> str:
        """Build a context note from extracted entities."""
        parts = []

        if entities.get("countries"):
            countries = [c.get("name", c.get("iso3", "")) for c in entities["countries"]]
            parts.append(f"Previously discussed countries: {', '.join(countries)}")

        if entities.get("indicators"):
            indicators = [i.get("name", i.get("code", "")) for i in entities["indicators"]]
            parts.append(f"Previously discussed indicators: {', '.join(indicators)}")

        if entities.get("time_period"):
            tp = entities["time_period"]
            parts.append(f"Time period context: {tp.get('start', '')} to {tp.get('end', '')}")

        if parts:
            return "[Context from conversation:\n" + "\n".join(parts) + "]"
        return ""

    async def _process_response(
        self, response, context: dict, message_id: str
    ) -> QueryResult:
        """Process Claude's response, executing any tool calls."""
        content_parts = []
        data = None
        visualization = None
        tool_calls = []
        sources = []

        for block in response.content:
            if block.type == "text":
                content_parts.append(block.text)

            elif block.type == "tool_use":
                # Execute the tool
                tool_calls.append(
                    {"name": block.name, "id": block.id, "input": block.input}
                )

                try:
                    result = await self.executor.execute(block.name, block.input)

                    # If this returned data, store it
                    if block.name == ToolName.FETCH_ECONOMIC_DATA:
                        data = result

                        # Determine visualization
                        viz_config = self.viz_selector.select(
                            query_type="time_series", data=result
                        )
                        visualization = viz_config

                        # Add source
                        sources.append(
                            {
                                "type": "world_bank",
                                "indicator": result.get("indicator", {}),
                                "url": "https://data.worldbank.org",
                            }
                        )

                    elif block.name == ToolName.SEARCH_DOCUMENTS:
                        # Add document sources
                        for doc in result.get("documents", []):
                            sources.append(
                                {
                                    "type": "document",
                                    "title": doc.get("title"),
                                    "url": doc.get("url"),
                                }
                            )

                except Exception as e:
                    content_parts.append(f"\n[Error executing {block.name}: {str(e)}]")

        # Generate follow-up suggestions
        followups = self._generate_followups(context, data)

        return QueryResult(
            message_id=message_id,
            content="".join(content_parts),
            data=data,
            visualization=visualization,
            sources=sources if sources else None,
            suggested_followups=followups,
            tool_calls=tool_calls,
        )

    def _generate_followups(
        self, context: dict, data: Optional[dict]
    ) -> list[str]:
        """Generate suggested follow-up questions."""
        followups = []

        if data:
            countries = data.get("countries", [])
            indicator = data.get("indicator", {})

            if len(countries) == 1:
                country_name = countries[0].get("name", "this country")
                followups.append(f"Compare {country_name} with regional peers")
                followups.append(f"What's driving {indicator.get('name', 'this trend')}?")
                followups.append(f"Show other economic indicators for {country_name}")

            elif len(countries) > 1:
                followups.append("Which country is performing best?")
                followups.append("Show the trend over time")

            # Add indicator-specific suggestions
            if "GDP" in indicator.get("name", ""):
                followups.append("What about inflation and employment?")
            elif "inflation" in indicator.get("name", "").lower():
                followups.append("Show monetary policy indicators")

        return followups[:4]  # Limit to 4 suggestions

    async def _process_fallback(
        self, query: str, context: dict, message_id: str
    ) -> QueryResult:
        """Fallback processing when Claude API is not available."""
        # This would use the existing rule-based query interpreter
        return QueryResult(
            message_id=message_id,
            content="AI orchestration requires an Anthropic API key. Please configure ANTHROPIC_API_KEY in your environment.",
            suggested_followups=[
                "Set up API key to enable intelligent queries"
            ],
        )

    async def _stream_fallback(self, query: str, context: dict) -> AsyncGenerator[dict, None]:
        """Fallback streaming when Claude API is not available."""
        yield {
            "type": "content",
            "content": "AI orchestration requires an Anthropic API key. Using basic query processing.",
        }

        # Use existing query interpreter logic
        from app.data.worldbank import WorldBankClient

        client = WorldBankClient()

        # Try to parse basic queries
        # This is a simplified version - the full implementation would
        # use the existing query-interpreter logic from the frontend

        yield {"type": "done"}
