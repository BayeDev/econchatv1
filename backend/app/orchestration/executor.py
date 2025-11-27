"""Tool Executor - Executes tool calls from Claude.

This module handles the actual execution of tools that Claude decides to use.
Each tool maps to a specific capability (data fetching, document search, etc.)
"""

from typing import Any, Optional
from datetime import datetime

from app.orchestration.tools import ToolName
from app.data.worldbank import WorldBankClient
from app.data.unified import UnifiedDataClient
from app.visualization.selector import VisualizationSelector


class ToolExecutor:
    """Executes tool calls and returns results."""

    def __init__(self):
        self.worldbank = WorldBankClient()
        self.unified = UnifiedDataClient()
        self.viz_selector = VisualizationSelector()

    async def execute(self, tool_name: str, params: dict) -> Any:
        """Execute a tool and return the result."""
        tool_handlers = {
            ToolName.FETCH_ECONOMIC_DATA: self._fetch_economic_data,
            ToolName.SEARCH_DOCUMENTS: self._search_documents,
            ToolName.COMPARE_COUNTRIES: self._compare_countries,
            ToolName.ANALYZE_TREND: self._analyze_trend,
            ToolName.GET_COUNTRY_PROFILE: self._get_country_profile,
            ToolName.SEARCH_INDICATORS: self._search_indicators,
            ToolName.CALCULATE_STATISTICS: self._calculate_statistics,
            ToolName.GENERATE_VISUALIZATION: self._generate_visualization,
        }

        handler = tool_handlers.get(tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_name}")

        return await handler(params)

    async def _fetch_economic_data(self, params: dict) -> dict:
        """Fetch economic data from World Bank API."""
        countries = params.get("countries", [])
        indicator = params.get("indicator")
        start_year = params.get("start_year", datetime.now().year - 10)
        end_year = params.get("end_year", datetime.now().year)

        if not countries or not indicator:
            raise ValueError("countries and indicator are required")

        # Fetch data from World Bank
        data = await self.worldbank.fetch_data(
            countries=countries,
            indicator=indicator,
            start_year=start_year,
            end_year=end_year,
        )

        # Get regional average for context if single country
        regional_data = None
        if len(countries) == 1:
            region = await self.worldbank.get_country_region(countries[0])
            if region:
                regional_data = await self.worldbank.fetch_regional_average(
                    region_code=region,
                    indicator=indicator,
                    start_year=start_year,
                    end_year=end_year,
                )

        # Generate narrative
        narrative = self._generate_narrative(data, regional_data)

        return {
            **data,
            "narrative": narrative,
            "regional_comparison": regional_data,
        }

    async def _search_documents(self, params: dict) -> dict:
        """Search internal documents."""
        query = params.get("query")
        doc_types = params.get("document_types")
        country = params.get("country")
        max_results = params.get("max_results", 5)

        # TODO: Implement Google Drive search
        # For now, return placeholder
        return {
            "documents": [],
            "message": "Document search not yet implemented. Configure Google Drive integration.",
        }

    async def _compare_countries(self, params: dict) -> dict:
        """Compare countries across indicators."""
        countries = params.get("countries", [])
        indicators = params.get("indicators", [])
        year = params.get("year")
        include_regional = params.get("include_regional_average", True)

        if len(countries) < 2:
            raise ValueError("At least 2 countries required for comparison")

        results = {}
        for indicator in indicators:
            data = await self.worldbank.fetch_data(
                countries=countries,
                indicator=indicator,
                start_year=year or datetime.now().year - 1,
                end_year=year or datetime.now().year,
            )
            results[indicator] = data

        return {
            "comparison": results,
            "countries": countries,
            "indicators": indicators,
            "year": year or datetime.now().year,
        }

    async def _analyze_trend(self, params: dict) -> dict:
        """Perform trend analysis on data."""
        country = params.get("country")
        indicator = params.get("indicator")
        period_years = params.get("period_years", 10)
        analysis_type = params.get("analysis_type", "simple")

        end_year = datetime.now().year
        start_year = end_year - period_years

        data = await self.worldbank.fetch_data(
            countries=[country],
            indicator=indicator,
            start_year=start_year,
            end_year=end_year,
        )

        # Calculate trend statistics
        points = data.get("data", [])
        values = [p["value"] for p in points if p.get("value") is not None]

        if len(values) < 2:
            return {
                "data": data,
                "trend": {
                    "direction": "insufficient_data",
                    "message": "Not enough data points for trend analysis",
                },
            }

        # Simple trend analysis
        first_value = values[0]
        last_value = values[-1]
        change = last_value - first_value
        pct_change = (change / abs(first_value)) * 100 if first_value != 0 else 0

        # Determine trend direction
        if pct_change > 5:
            direction = "increasing"
        elif pct_change < -5:
            direction = "decreasing"
        else:
            direction = "stable"

        # Calculate average and volatility
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        volatility = (std_dev / abs(avg)) * 100 if avg != 0 else 0

        return {
            "data": data,
            "trend": {
                "direction": direction,
                "start_value": first_value,
                "end_value": last_value,
                "absolute_change": change,
                "percent_change": round(pct_change, 2),
                "average": round(avg, 2),
                "volatility": round(volatility, 2),
                "data_points": len(values),
            },
        }

    async def _get_country_profile(self, params: dict) -> dict:
        """Get comprehensive country economic profile."""
        country = params.get("country")
        profile_type = params.get("profile_type", "overview")

        # Define indicators for each profile type
        profile_indicators = {
            "overview": [
                "NY.GDP.MKTP.KD.ZG",  # GDP growth
                "FP.CPI.TOTL.ZG",  # Inflation
                "SL.UEM.TOTL.ZS",  # Unemployment
                "BN.CAB.XOKA.GD.ZS",  # Current account
            ],
            "fiscal": [
                "GC.DOD.TOTL.GD.ZS",  # Debt
                "GC.REV.XGRT.GD.ZS",  # Revenue
                "GC.XPN.TOTL.GD.ZS",  # Expenditure
                "GC.BAL.CASH.GD.ZS",  # Fiscal balance
            ],
            "trade": [
                "NE.EXP.GNFS.ZS",  # Exports
                "NE.IMP.GNFS.ZS",  # Imports
                "NE.TRD.GNFS.ZS",  # Trade openness
                "BX.KLT.DINV.WD.GD.ZS",  # FDI
            ],
            "social": [
                "SI.POV.DDAY",  # Poverty
                "SP.DYN.LE00.IN",  # Life expectancy
                "SE.ADT.LITR.ZS",  # Literacy
                "SI.POV.GINI",  # Inequality
            ],
        }

        if profile_type == "full":
            indicators = []
            for ind_list in profile_indicators.values():
                indicators.extend(ind_list)
        else:
            indicators = profile_indicators.get(profile_type, profile_indicators["overview"])

        # Fetch data for all indicators
        profile_data = {}
        current_year = datetime.now().year

        for indicator in indicators:
            try:
                data = await self.worldbank.fetch_data(
                    countries=[country],
                    indicator=indicator,
                    start_year=current_year - 5,
                    end_year=current_year,
                )
                profile_data[indicator] = data
            except Exception:
                continue  # Skip failed indicators

        # Get country metadata
        country_info = await self.worldbank.get_country_info(country)

        return {
            "country": country_info,
            "profile_type": profile_type,
            "indicators": profile_data,
            "generated_at": datetime.now().isoformat(),
        }

    async def _search_indicators(self, params: dict) -> dict:
        """Search available indicators."""
        query = params.get("query", "")
        category = params.get("category")

        # Define indicator catalog
        indicators = [
            {"code": "NY.GDP.MKTP.KD.ZG", "name": "GDP growth (annual %)", "category": "economic"},
            {"code": "NY.GDP.MKTP.CD", "name": "GDP (current US$)", "category": "economic"},
            {"code": "NY.GDP.PCAP.CD", "name": "GDP per capita (current US$)", "category": "economic"},
            {"code": "FP.CPI.TOTL.ZG", "name": "Inflation, consumer prices (annual %)", "category": "economic"},
            {"code": "SL.UEM.TOTL.ZS", "name": "Unemployment, total (% of labor force)", "category": "social"},
            {"code": "NE.EXP.GNFS.ZS", "name": "Exports of goods and services (% of GDP)", "category": "trade"},
            {"code": "NE.IMP.GNFS.ZS", "name": "Imports of goods and services (% of GDP)", "category": "trade"},
            {"code": "GC.DOD.TOTL.GD.ZS", "name": "Central government debt, total (% of GDP)", "category": "fiscal"},
            {"code": "BX.KLT.DINV.WD.GD.ZS", "name": "Foreign direct investment, net inflows (% of GDP)", "category": "trade"},
            {"code": "SI.POV.DDAY", "name": "Poverty headcount ratio at $2.15 a day", "category": "social"},
            {"code": "SP.DYN.LE00.IN", "name": "Life expectancy at birth, total (years)", "category": "social"},
            {"code": "SI.POV.GINI", "name": "Gini index", "category": "social"},
        ]

        # Filter by query
        if query:
            query_lower = query.lower()
            indicators = [
                i for i in indicators
                if query_lower in i["name"].lower() or query_lower in i["code"].lower()
            ]

        # Filter by category
        if category:
            indicators = [i for i in indicators if i["category"] == category]

        return {
            "indicators": indicators,
            "total": len(indicators),
        }

    async def _calculate_statistics(self, params: dict) -> dict:
        """Calculate statistics on data."""
        # This would operate on previously fetched data
        # For now, return structure
        return {
            "statistics": params.get("statistics", []),
            "message": "Statistics calculation based on context data",
        }

    async def _generate_visualization(self, params: dict) -> dict:
        """Generate visualization configuration."""
        data_type = params.get("data_type", "time_series")
        num_countries = params.get("num_countries", 1)
        num_years = params.get("num_years", 10)
        user_pref = params.get("user_preference")

        config = self.viz_selector.select(
            query_type=data_type,
            num_countries=num_countries,
            num_years=num_years,
            user_preference=user_pref,
        )

        return config

    def _generate_narrative(self, data: dict, regional_data: Optional[dict] = None) -> dict:
        """Generate narrative analysis of the data."""
        points = data.get("data", [])
        indicator = data.get("indicator", {})

        if not points:
            return {
                "summary": "No data available for the requested query.",
                "trend_description": "",
                "notable_flags": ["No data available"],
            }

        # Get valid values
        valid_points = [p for p in points if p.get("value") is not None]
        if not valid_points:
            return {
                "summary": "Data points exist but all values are null.",
                "trend_description": "",
                "notable_flags": ["Missing values"],
            }

        # Sort by year
        valid_points.sort(key=lambda x: x["year"])

        oldest = valid_points[0]
        latest = valid_points[-1]

        # Calculate change
        change = latest["value"] - oldest["value"]
        if oldest["value"] != 0:
            pct_change = (change / abs(oldest["value"])) * 100
        else:
            pct_change = 0

        # Build summary
        country = latest.get("country", "The country")
        indicator_name = indicator.get("name", "This indicator")

        direction = "increased" if change > 0 else "decreased"
        summary = f"{country}'s {indicator_name} was {latest['value']:.1f}% in {latest['year']}, {direction} from {oldest['value']:.1f}% in {oldest['year']}."

        # Trend description
        trend = f"{indicator_name} {direction} by {abs(change):.1f} percentage points from {oldest['year']} to {latest['year']}."

        # Regional comparison
        peer_comparison = None
        if regional_data and regional_data.get("data"):
            regional_points = [p for p in regional_data["data"] if p.get("value") is not None]
            if regional_points:
                regional_latest = max(regional_points, key=lambda x: x["year"])
                if regional_latest["value"] is not None:
                    comparison = "above" if latest["value"] > regional_latest["value"] else "below"
                    peer_comparison = f"This is {comparison} the regional average of {regional_latest['value']:.1f}%."

        # Notable flags
        flags = []

        # Check for volatility
        if len(valid_points) > 3:
            values = [p["value"] for p in valid_points]
            avg = sum(values) / len(values)
            variance = sum((v - avg) ** 2 for v in values) / len(values)
            std_dev = variance ** 0.5
            if std_dev > abs(avg) * 0.5:  # High volatility
                flags.append("High volatility over the period")

        # Check for peak/trough
        values = [p["value"] for p in valid_points]
        if latest["value"] == max(values):
            flags.append("Currently at highest level in period")
        elif latest["value"] == min(values):
            flags.append("Currently at lowest level in period")

        return {
            "summary": summary,
            "trend_description": trend,
            "peer_comparison": peer_comparison,
            "notable_flags": flags,
        }
