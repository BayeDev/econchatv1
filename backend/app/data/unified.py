"""Unified Data Client - Single interface for all data sources.

This module provides a unified interface for fetching data from
multiple sources (World Bank, IMF, internal documents, etc.)
"""

from typing import Optional, Literal
from enum import Enum

from app.data.worldbank import WorldBankClient


class DataSource(str, Enum):
    """Available data sources."""

    WORLD_BANK = "world_bank"
    IMF = "imf"
    INTERNAL = "internal"
    OECD = "oecd"


class UnifiedDataClient:
    """Unified interface for all data sources."""

    def __init__(self):
        self.worldbank = WorldBankClient()
        # Future: Add other clients
        # self.imf = IMFClient()
        # self.gdrive = GoogleDriveClient()

    async def fetch_indicator(
        self,
        countries: list[str],
        indicator: str,
        start_year: int,
        end_year: int,
        source: DataSource = DataSource.WORLD_BANK,
    ) -> dict:
        """
        Fetch indicator data from the appropriate source.

        Automatically routes to the correct data source based on
        indicator code or explicit source parameter.
        """
        # For now, route everything to World Bank
        # Future: Route based on indicator prefix or source param

        if source == DataSource.WORLD_BANK:
            return await self.worldbank.fetch_data(
                countries=countries,
                indicator=indicator,
                start_year=start_year,
                end_year=end_year,
            )

        # Placeholder for other sources
        raise NotImplementedError(f"Data source {source} not yet implemented")

    async def search_all_sources(
        self,
        query: str,
        sources: Optional[list[DataSource]] = None,
    ) -> dict:
        """
        Search across multiple data sources.

        Args:
            query: Search query
            sources: List of sources to search (all if None)

        Returns:
            Combined results from all sources
        """
        sources = sources or list(DataSource)
        results = {"sources": {}}

        for source in sources:
            try:
                if source == DataSource.WORLD_BANK:
                    # Search World Bank indicators
                    # This would search indicator names/descriptions
                    results["sources"]["world_bank"] = {
                        "type": "indicators",
                        "results": [],  # TODO: Implement search
                    }
                elif source == DataSource.INTERNAL:
                    # Search internal documents
                    results["sources"]["internal"] = {
                        "type": "documents",
                        "results": [],  # TODO: Implement GDrive search
                    }
            except Exception as e:
                results["sources"][source.value] = {
                    "error": str(e),
                }

        return results

    async def get_data_availability(
        self,
        country: str,
        indicators: list[str],
    ) -> dict:
        """
        Check data availability for a country across indicators.

        Useful for understanding what data exists before querying.
        """
        availability = {}

        for indicator in indicators:
            try:
                data = await self.worldbank.fetch_data(
                    countries=[country],
                    indicator=indicator,
                    start_year=2000,
                    end_year=2024,
                )

                points = data.get("data", [])
                valid_points = [p for p in points if p.get("value") is not None]

                availability[indicator] = {
                    "available": len(valid_points) > 0,
                    "data_points": len(valid_points),
                    "years": sorted([p["year"] for p in valid_points]) if valid_points else [],
                    "latest_year": max(p["year"] for p in valid_points) if valid_points else None,
                }

            except Exception:
                availability[indicator] = {
                    "available": False,
                    "error": "Failed to check availability",
                }

        return availability

    async def close(self):
        """Close all clients."""
        await self.worldbank.close()
