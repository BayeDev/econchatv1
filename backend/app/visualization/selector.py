"""Visualization Selector - Intelligent chart type selection.

This module determines the optimal visualization type based on:
- Data characteristics (time series, comparison, distribution)
- Number of data points and dimensions
- User preferences (if specified)
- Query type and intent
"""

from typing import Optional, Literal
from dataclasses import dataclass
from enum import Enum


class ChartType(str, Enum):
    """Available chart types."""

    LINE = "line"
    BAR = "bar"
    AREA = "area"
    SCATTER = "scatter"
    PIE = "pie"
    MAP = "map"
    TABLE = "table"
    MULTI_LINE = "multi_line"
    STACKED_BAR = "stacked_bar"
    GROUPED_BAR = "grouped_bar"
    HEATMAP = "heatmap"


@dataclass
class VisualizationConfig:
    """Configuration for a visualization."""

    chart_type: ChartType
    title: str
    x_axis: str
    y_axis: str
    legend_position: str = "bottom"
    show_grid: bool = True
    show_tooltip: bool = True
    color_scheme: str = "default"
    annotations: list = None
    interactive: bool = True

    def to_dict(self) -> dict:
        return {
            "chartType": self.chart_type.value,
            "title": self.title,
            "xAxis": self.x_axis,
            "yAxis": self.y_axis,
            "legendPosition": self.legend_position,
            "showGrid": self.show_grid,
            "showTooltip": self.show_tooltip,
            "colorScheme": self.color_scheme,
            "annotations": self.annotations or [],
            "interactive": self.interactive,
        }


class VisualizationSelector:
    """Selects optimal visualization based on data and context."""

    def select(
        self,
        query_type: str = "time_series",
        data: Optional[dict] = None,
        num_countries: int = 1,
        num_years: int = 10,
        user_preference: Optional[str] = None,
    ) -> dict:
        """
        Select the best visualization for the data.

        Args:
            query_type: Type of query (time_series, comparison, etc.)
            data: The actual data to visualize
            num_countries: Number of countries in data
            num_years: Number of time points
            user_preference: User's explicit preference if any

        Returns:
            Visualization configuration dictionary
        """
        # If user has explicit preference, honor it
        if user_preference:
            return self._get_user_preferred(user_preference, data)

        # Extract data characteristics if data provided
        if data:
            num_countries = len(data.get("countries", [])) or num_countries
            points = data.get("data", [])
            if points:
                years = set(p.get("year") for p in points)
                num_years = len(years)

        # Select based on query type and data characteristics
        config = self._select_by_type(query_type, num_countries, num_years, data)

        return config.to_dict()

    def _select_by_type(
        self,
        query_type: str,
        num_countries: int,
        num_years: int,
        data: Optional[dict],
    ) -> VisualizationConfig:
        """Select visualization based on query type."""

        indicator = data.get("indicator", {}) if data else {}
        indicator_name = indicator.get("name", "Value")
        unit = indicator.get("unit", "")

        # Time series analysis
        if query_type in ["time_series", "trend"]:
            if num_countries == 1:
                # Single country trend - line chart
                return VisualizationConfig(
                    chart_type=ChartType.LINE,
                    title=f"{indicator_name} Over Time",
                    x_axis="Year",
                    y_axis=f"{indicator_name} ({unit})" if unit else indicator_name,
                    color_scheme="single",
                )
            else:
                # Multiple countries over time - multi-line chart
                return VisualizationConfig(
                    chart_type=ChartType.MULTI_LINE,
                    title=f"{indicator_name} Comparison",
                    x_axis="Year",
                    y_axis=f"{indicator_name} ({unit})" if unit else indicator_name,
                    legend_position="right",
                    color_scheme="categorical",
                )

        # Country comparison
        elif query_type == "comparison":
            if num_years <= 3:
                # Few time points - grouped bar chart
                return VisualizationConfig(
                    chart_type=ChartType.GROUPED_BAR,
                    title=f"{indicator_name} by Country",
                    x_axis="Country",
                    y_axis=f"{indicator_name} ({unit})" if unit else indicator_name,
                    color_scheme="categorical",
                )
            else:
                # Many time points - multi-line
                return VisualizationConfig(
                    chart_type=ChartType.MULTI_LINE,
                    title=f"{indicator_name} Trends",
                    x_axis="Year",
                    y_axis=f"{indicator_name} ({unit})" if unit else indicator_name,
                    legend_position="right",
                )

        # Distribution analysis
        elif query_type == "distribution":
            return VisualizationConfig(
                chart_type=ChartType.BAR,
                title=f"Distribution of {indicator_name}",
                x_axis="Country",
                y_axis=f"{indicator_name} ({unit})" if unit else indicator_name,
                color_scheme="gradient",
            )

        # Geographic analysis
        elif query_type == "geographic":
            return VisualizationConfig(
                chart_type=ChartType.MAP,
                title=f"{indicator_name} by Region",
                x_axis="",
                y_axis="",
                color_scheme="heat",
            )

        # Correlation analysis
        elif query_type == "correlation":
            return VisualizationConfig(
                chart_type=ChartType.SCATTER,
                title="Correlation Analysis",
                x_axis="Indicator 1",
                y_axis="Indicator 2",
                color_scheme="categorical",
            )

        # Default fallback
        else:
            # Use simple line for single country, bar for multiple
            if num_countries == 1:
                return VisualizationConfig(
                    chart_type=ChartType.LINE,
                    title=indicator_name,
                    x_axis="Year",
                    y_axis=f"{indicator_name} ({unit})" if unit else indicator_name,
                )
            else:
                if num_years > 3:
                    return VisualizationConfig(
                        chart_type=ChartType.MULTI_LINE,
                        title=indicator_name,
                        x_axis="Year",
                        y_axis=f"{indicator_name} ({unit})" if unit else indicator_name,
                        legend_position="right",
                    )
                else:
                    return VisualizationConfig(
                        chart_type=ChartType.BAR,
                        title=indicator_name,
                        x_axis="Country",
                        y_axis=f"{indicator_name} ({unit})" if unit else indicator_name,
                    )

    def _get_user_preferred(
        self, preference: str, data: Optional[dict]
    ) -> dict:
        """Get configuration for user-specified visualization type."""

        indicator = data.get("indicator", {}) if data else {}
        indicator_name = indicator.get("name", "Value")
        unit = indicator.get("unit", "")

        preference_lower = preference.lower()

        type_mapping = {
            "line": ChartType.LINE,
            "bar": ChartType.BAR,
            "area": ChartType.AREA,
            "scatter": ChartType.SCATTER,
            "pie": ChartType.PIE,
            "table": ChartType.TABLE,
            "map": ChartType.MAP,
            "heatmap": ChartType.HEATMAP,
        }

        chart_type = type_mapping.get(preference_lower, ChartType.LINE)

        config = VisualizationConfig(
            chart_type=chart_type,
            title=indicator_name,
            x_axis="Year" if chart_type in [ChartType.LINE, ChartType.AREA] else "Category",
            y_axis=f"{indicator_name} ({unit})" if unit else indicator_name,
        )

        return config.to_dict()

    def add_annotations(
        self,
        config: dict,
        data: dict,
        events: Optional[list[dict]] = None,
    ) -> dict:
        """
        Add contextual annotations to visualization.

        Args:
            config: Base visualization config
            data: The data being visualized
            events: Optional list of events to annotate (policy changes, etc.)

        Returns:
            Config with annotations added
        """
        annotations = []

        # Auto-detect notable points in data
        points = data.get("data", [])
        if points:
            values = [p["value"] for p in points if p.get("value") is not None]
            if values:
                max_val = max(values)
                min_val = min(values)

                max_point = next(p for p in points if p.get("value") == max_val)
                min_point = next(p for p in points if p.get("value") == min_val)

                annotations.append({
                    "type": "point",
                    "x": max_point["year"],
                    "y": max_val,
                    "label": f"Peak: {max_val:.1f}",
                })

                annotations.append({
                    "type": "point",
                    "x": min_point["year"],
                    "y": min_val,
                    "label": f"Low: {min_val:.1f}",
                })

        # Add external events if provided
        if events:
            for event in events:
                annotations.append({
                    "type": "event",
                    "x": event["year"],
                    "label": event["description"],
                })

        config["annotations"] = annotations
        return config
