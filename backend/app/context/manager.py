"""Context Manager - Handles conversation memory and context retrieval.

This module manages:
1. Session-based conversation history
2. Entity extraction and tracking (countries, indicators, time periods)
3. User preferences and patterns
4. Semantic context retrieval (RAG) for relevant information
"""

from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import re


@dataclass
class Entity:
    """Represents an extracted entity."""

    type: str  # country, indicator, time_period, etc.
    value: Any
    confidence: float = 1.0
    source_query: Optional[str] = None


@dataclass
class ConversationContext:
    """Context accumulated from a conversation."""

    session_id: str
    countries: list[dict] = field(default_factory=list)
    indicators: list[dict] = field(default_factory=list)
    time_period: Optional[dict] = None
    history: list[dict] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    last_query: Optional[str] = None
    last_data: Optional[dict] = None


# In-memory context store (will be replaced with database)
context_store: dict[str, ConversationContext] = {}


class ContextManager:
    """Manages conversation context and memory."""

    def __init__(self):
        # Country name to ISO3 mapping (subset for demo)
        self.country_mapping = {
            "nigeria": "NGA",
            "kenya": "KEN",
            "ghana": "GHA",
            "south africa": "ZAF",
            "egypt": "EGY",
            "morocco": "MAR",
            "ethiopia": "ETH",
            "tanzania": "TZA",
            "uganda": "UGA",
            "rwanda": "RWA",
            "senegal": "SEN",
            "ivory coast": "CIV",
            "cote d'ivoire": "CIV",
            "cameroon": "CMR",
            "dr congo": "COD",
            "angola": "AGO",
            "mozambique": "MOZ",
            "zambia": "ZMB",
            "zimbabwe": "ZWE",
            "botswana": "BWA",
            "namibia": "NAM",
            "mauritius": "MUS",
            "sierra leone": "SLE",
            "liberia": "LBR",
            "mali": "MLI",
            "burkina faso": "BFA",
            "niger": "NER",
            "chad": "TCD",
            "sudan": "SDN",
            "tunisia": "TUN",
            "algeria": "DZA",
            "libya": "LBY",
        }

        # Indicator keyword mapping
        self.indicator_mapping = {
            "gdp growth": {"code": "NY.GDP.MKTP.KD.ZG", "name": "GDP Growth", "unit": "% annual"},
            "gdp": {"code": "NY.GDP.MKTP.CD", "name": "GDP", "unit": "current USD"},
            "economic growth": {"code": "NY.GDP.MKTP.KD.ZG", "name": "GDP Growth", "unit": "% annual"},
            "inflation": {"code": "FP.CPI.TOTL.ZG", "name": "Inflation", "unit": "% annual"},
            "unemployment": {"code": "SL.UEM.TOTL.ZS", "name": "Unemployment", "unit": "% of labor force"},
            "poverty": {"code": "SI.POV.DDAY", "name": "Poverty", "unit": "% of population"},
            "debt": {"code": "GC.DOD.TOTL.GD.ZS", "name": "Government Debt", "unit": "% of GDP"},
            "exports": {"code": "NE.EXP.GNFS.ZS", "name": "Exports", "unit": "% of GDP"},
            "imports": {"code": "NE.IMP.GNFS.ZS", "name": "Imports", "unit": "% of GDP"},
            "fdi": {"code": "BX.KLT.DINV.WD.GD.ZS", "name": "FDI Inflows", "unit": "% of GDP"},
            "trade": {"code": "NE.TRD.GNFS.ZS", "name": "Trade Openness", "unit": "% of GDP"},
            "current account": {"code": "BN.CAB.XOKA.GD.ZS", "name": "Current Account", "unit": "% of GDP"},
            "life expectancy": {"code": "SP.DYN.LE00.IN", "name": "Life Expectancy", "unit": "years"},
            "population": {"code": "SP.POP.TOTL", "name": "Population", "unit": "total"},
        }

    async def get_context(self, session_id: Optional[str]) -> dict:
        """
        Get the current context for a session.

        Args:
            session_id: The session ID to get context for

        Returns:
            Context dictionary with entities, history, and preferences
        """
        if not session_id:
            return {
                "entities": {},
                "history": [],
                "preferences": {},
            }

        ctx = context_store.get(session_id)
        if not ctx:
            return {
                "entities": {},
                "history": [],
                "preferences": {},
            }

        return {
            "entities": {
                "countries": ctx.countries,
                "indicators": ctx.indicators,
                "time_period": ctx.time_period,
            },
            "history": ctx.history[-20:],  # Last 20 messages
            "preferences": ctx.preferences,
            "last_query": ctx.last_query,
            "last_data": ctx.last_data,
        }

    async def save_message(
        self,
        session_id: str,
        query: str,
        response: dict,
    ) -> None:
        """
        Save a message exchange to the context.

        Args:
            session_id: The session ID
            query: The user's query
            response: The assistant's response
        """
        if session_id not in context_store:
            context_store[session_id] = ConversationContext(session_id=session_id)

        ctx = context_store[session_id]

        # Add to history
        ctx.history.append({
            "role": "user",
            "content": query,
            "timestamp": datetime.now().isoformat(),
        })

        ctx.history.append({
            "role": "assistant",
            "content": response.get("content", ""),
            "data": response.get("data"),
            "timestamp": datetime.now().isoformat(),
        })

        # Extract and update entities from query
        await self._extract_entities(ctx, query)

        # Update last query and data
        ctx.last_query = query
        if response.get("data"):
            ctx.last_data = response["data"]

    async def _extract_entities(
        self, ctx: ConversationContext, query: str
    ) -> None:
        """Extract entities from a query and update context."""
        query_lower = query.lower()

        # Extract countries
        for name, code in self.country_mapping.items():
            if name in query_lower:
                country = {"name": name.title(), "iso3": code}
                if country not in ctx.countries:
                    ctx.countries.append(country)

        # Extract indicators
        for keyword, indicator in self.indicator_mapping.items():
            if keyword in query_lower:
                if indicator not in ctx.indicators:
                    ctx.indicators.append(indicator)

        # Extract time periods
        time_period = self._extract_time_period(query_lower)
        if time_period:
            ctx.time_period = time_period

    def _extract_time_period(self, query: str) -> Optional[dict]:
        """Extract time period from query."""
        current_year = datetime.now().year

        # Pattern: "2015-2023" or "2015 to 2023"
        range_match = re.search(r'(\d{4})\s*[-–to]+\s*(\d{4})', query)
        if range_match:
            return {
                "start": int(range_match.group(1)),
                "end": int(range_match.group(2)),
            }

        # Pattern: "since 2015"
        since_match = re.search(r'since\s+(\d{4})', query)
        if since_match:
            return {
                "start": int(since_match.group(1)),
                "end": current_year,
            }

        # Pattern: "last N years"
        last_years_match = re.search(r'last\s+(\d+)\s+years?', query)
        if last_years_match:
            years = int(last_years_match.group(1))
            return {
                "start": current_year - years,
                "end": current_year,
            }

        # Pattern: "past N years"
        past_years_match = re.search(r'past\s+(\d+)\s+years?', query)
        if past_years_match:
            years = int(past_years_match.group(1))
            return {
                "start": current_year - years,
                "end": current_year,
            }

        # Pattern: "N decades"
        decades_match = re.search(r'(\d+)\s*decades?', query)
        if decades_match:
            decades = int(decades_match.group(1))
            return {
                "start": current_year - (decades * 10),
                "end": current_year,
            }

        return None

    async def update_preferences(
        self,
        session_id: str,
        preferences: dict,
    ) -> None:
        """Update user preferences for a session."""
        if session_id not in context_store:
            context_store[session_id] = ConversationContext(session_id=session_id)

        ctx = context_store[session_id]
        ctx.preferences.update(preferences)

    async def clear_context(self, session_id: str) -> None:
        """Clear context for a session."""
        if session_id in context_store:
            del context_store[session_id]

    async def get_relevant_history(
        self,
        session_id: str,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        """
        Get relevant history messages based on semantic similarity.

        For now, returns recent messages. Future: Use embeddings for RAG.
        """
        ctx = context_store.get(session_id)
        if not ctx:
            return []

        # Simple relevance: return most recent messages
        # TODO: Implement semantic similarity with embeddings
        return ctx.history[-limit:]

    def get_context_summary(self, session_id: str) -> str:
        """
        Generate a text summary of the current context.

        Useful for including in prompts to Claude.
        """
        ctx = context_store.get(session_id)
        if not ctx:
            return ""

        parts = []

        if ctx.countries:
            country_names = [c["name"] for c in ctx.countries]
            parts.append(f"Countries discussed: {', '.join(country_names)}")

        if ctx.indicators:
            indicator_names = [i["name"] for i in ctx.indicators]
            parts.append(f"Indicators mentioned: {', '.join(indicator_names)}")

        if ctx.time_period:
            parts.append(f"Time period: {ctx.time_period['start']} to {ctx.time_period['end']}")

        if ctx.last_query:
            parts.append(f"Previous query: {ctx.last_query}")

        return " | ".join(parts) if parts else "New conversation"
