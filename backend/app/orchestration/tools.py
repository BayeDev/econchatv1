"""Tool definitions for Claude function calling.

These tools define the capabilities available to the AI for executing
user queries. Each tool has:
- A name and description for Claude to understand when to use it
- Input parameters with types and descriptions
- An execute function that performs the actual operation
"""

from typing import Any, Optional
from dataclasses import dataclass
from enum import Enum


class ToolName(str, Enum):
    """Available tool names."""

    FETCH_ECONOMIC_DATA = "fetch_economic_data"
    SEARCH_DOCUMENTS = "search_documents"
    COMPARE_COUNTRIES = "compare_countries"
    ANALYZE_TREND = "analyze_trend"
    GET_COUNTRY_PROFILE = "get_country_profile"
    SEARCH_INDICATORS = "search_indicators"
    CALCULATE_STATISTICS = "calculate_statistics"
    GENERATE_VISUALIZATION = "generate_visualization"


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""

    name: str
    type: str
    description: str
    required: bool = True
    enum: Optional[list[str]] = None
    default: Any = None


@dataclass
class ToolDefinition:
    """Definition of a tool for Claude function calling."""

    name: str
    description: str
    parameters: list[ToolParameter]


# Tool definitions for Claude
TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name=ToolName.FETCH_ECONOMIC_DATA,
        description="""Fetch economic indicator data from World Bank or other sources.
        Use this when the user asks about specific economic metrics for countries.
        Examples: GDP growth, inflation rate, unemployment, trade balance, debt levels.""",
        parameters=[
            ToolParameter(
                name="countries",
                type="array",
                description="List of country ISO3 codes (e.g., ['NGA', 'KEN', 'ZAF'])",
            ),
            ToolParameter(
                name="indicator",
                type="string",
                description="World Bank indicator code (e.g., 'NY.GDP.MKTP.KD.ZG' for GDP growth)",
            ),
            ToolParameter(
                name="start_year",
                type="integer",
                description="Start year for data range",
                required=False,
                default=2014,
            ),
            ToolParameter(
                name="end_year",
                type="integer",
                description="End year for data range",
                required=False,
                default=2024,
            ),
        ],
    ),
    ToolDefinition(
        name=ToolName.SEARCH_DOCUMENTS,
        description="""Search internal documents (Google Drive, SharePoint) for relevant information.
        Use this when the user asks about internal reports, country strategies, project documents,
        or historical analyses that might be stored in organizational documents.""",
        parameters=[
            ToolParameter(
                name="query",
                type="string",
                description="Search query for finding relevant documents",
            ),
            ToolParameter(
                name="document_types",
                type="array",
                description="Types of documents to search",
                required=False,
                enum=["pdf", "docx", "xlsx", "pptx"],
            ),
            ToolParameter(
                name="country",
                type="string",
                description="Filter by country mentioned in documents",
                required=False,
            ),
            ToolParameter(
                name="max_results",
                type="integer",
                description="Maximum number of documents to return",
                required=False,
                default=5,
            ),
        ],
    ),
    ToolDefinition(
        name=ToolName.COMPARE_COUNTRIES,
        description="""Compare multiple countries across one or more economic indicators.
        Use this when the user wants to compare performance between countries or
        benchmark a country against peers.""",
        parameters=[
            ToolParameter(
                name="countries",
                type="array",
                description="List of country ISO3 codes to compare",
            ),
            ToolParameter(
                name="indicators",
                type="array",
                description="List of indicator codes to compare",
            ),
            ToolParameter(
                name="year",
                type="integer",
                description="Specific year for comparison (uses latest if not provided)",
                required=False,
            ),
            ToolParameter(
                name="include_regional_average",
                type="boolean",
                description="Whether to include regional averages for context",
                required=False,
                default=True,
            ),
        ],
    ),
    ToolDefinition(
        name=ToolName.ANALYZE_TREND,
        description="""Perform trend analysis on economic data over time.
        Use this when the user asks about trends, patterns, changes over time,
        or wants to understand the trajectory of an indicator.""",
        parameters=[
            ToolParameter(
                name="country",
                type="string",
                description="Country ISO3 code",
            ),
            ToolParameter(
                name="indicator",
                type="string",
                description="Indicator code to analyze",
            ),
            ToolParameter(
                name="period_years",
                type="integer",
                description="Number of years to analyze",
                required=False,
                default=10,
            ),
            ToolParameter(
                name="analysis_type",
                type="string",
                description="Type of trend analysis",
                required=False,
                enum=["simple", "moving_average", "regression", "decomposition"],
                default="simple",
            ),
        ],
    ),
    ToolDefinition(
        name=ToolName.GET_COUNTRY_PROFILE,
        description="""Get a comprehensive economic profile/snapshot for a country.
        Use this when the user asks general questions about a country's economy
        without specifying particular indicators.""",
        parameters=[
            ToolParameter(
                name="country",
                type="string",
                description="Country ISO3 code",
            ),
            ToolParameter(
                name="profile_type",
                type="string",
                description="Type of profile to generate",
                required=False,
                enum=["overview", "fiscal", "trade", "social", "full"],
                default="overview",
            ),
        ],
    ),
    ToolDefinition(
        name=ToolName.SEARCH_INDICATORS,
        description="""Search for available economic indicators by keyword or category.
        Use this when the user asks what data is available or searches for
        specific types of metrics.""",
        parameters=[
            ToolParameter(
                name="query",
                type="string",
                description="Search term for indicators",
            ),
            ToolParameter(
                name="category",
                type="string",
                description="Filter by indicator category",
                required=False,
                enum=[
                    "economic",
                    "fiscal",
                    "trade",
                    "social",
                    "environment",
                    "governance",
                ],
            ),
        ],
    ),
    ToolDefinition(
        name=ToolName.CALCULATE_STATISTICS,
        description="""Calculate statistical measures on economic data.
        Use this when the user asks for averages, growth rates, volatility,
        correlations, or other statistical analysis.""",
        parameters=[
            ToolParameter(
                name="data_source",
                type="string",
                description="Reference to previously fetched data or new query",
            ),
            ToolParameter(
                name="statistics",
                type="array",
                description="List of statistics to calculate",
                enum=[
                    "mean",
                    "median",
                    "std_dev",
                    "min",
                    "max",
                    "growth_rate",
                    "cagr",
                    "volatility",
                    "correlation",
                ],
            ),
        ],
    ),
    ToolDefinition(
        name=ToolName.GENERATE_VISUALIZATION,
        description="""Generate a visualization configuration for the data.
        Use this to determine the best chart type and configuration for displaying results.""",
        parameters=[
            ToolParameter(
                name="data_type",
                type="string",
                description="Type of data being visualized",
                enum=[
                    "time_series",
                    "comparison",
                    "distribution",
                    "correlation",
                    "geographic",
                ],
            ),
            ToolParameter(
                name="num_countries",
                type="integer",
                description="Number of countries in the data",
            ),
            ToolParameter(
                name="num_years",
                type="integer",
                description="Number of years/time points in the data",
            ),
            ToolParameter(
                name="user_preference",
                type="string",
                description="User's stated preference for visualization type",
                required=False,
            ),
        ],
    ),
]


def get_tools_for_claude() -> list[dict]:
    """Convert tool definitions to Claude API format."""
    tools = []

    for tool_def in TOOL_DEFINITIONS:
        # Build properties dict for parameters
        properties = {}
        required = []

        for param in tool_def.parameters:
            prop = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default

            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        tools.append(
            {
                "name": tool_def.name,
                "description": tool_def.description,
                "input_schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            }
        )

    return tools


# Indicator code mapping for natural language
INDICATOR_MAPPING = {
    # GDP
    "gdp growth": "NY.GDP.MKTP.KD.ZG",
    "gdp": "NY.GDP.MKTP.CD",
    "gdp per capita": "NY.GDP.PCAP.CD",
    "economic growth": "NY.GDP.MKTP.KD.ZG",
    # Inflation
    "inflation": "FP.CPI.TOTL.ZG",
    "cpi": "FP.CPI.TOTL.ZG",
    "consumer prices": "FP.CPI.TOTL.ZG",
    # Employment
    "unemployment": "SL.UEM.TOTL.ZS",
    "jobless": "SL.UEM.TOTL.ZS",
    # Trade
    "exports": "NE.EXP.GNFS.ZS",
    "imports": "NE.IMP.GNFS.ZS",
    "trade": "NE.TRD.GNFS.ZS",
    "current account": "BN.CAB.XOKA.GD.ZS",
    "fdi": "BX.KLT.DINV.WD.GD.ZS",
    # Fiscal
    "debt": "GC.DOD.TOTL.GD.ZS",
    "government debt": "GC.DOD.TOTL.GD.ZS",
    # Social
    "poverty": "SI.POV.DDAY",
    "life expectancy": "SP.DYN.LE00.IN",
    "population": "SP.POP.TOTL",
    "gini": "SI.POV.GINI",
    "inequality": "SI.POV.GINI",
}


def resolve_indicator(natural_query: str) -> Optional[str]:
    """Resolve natural language indicator reference to World Bank code."""
    query_lower = natural_query.lower()

    for phrase, code in INDICATOR_MAPPING.items():
        if phrase in query_lower:
            return code

    return None
