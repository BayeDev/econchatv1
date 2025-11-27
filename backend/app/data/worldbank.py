"""World Bank API client for fetching economic data."""

from typing import Optional
from datetime import datetime
import httpx

from app.config import get_settings

settings = get_settings()


# Indicator metadata
INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": {"name": "GDP Growth", "unit": "% annual"},
    "NY.GDP.MKTP.CD": {"name": "GDP (current USD)", "unit": "USD"},
    "NY.GDP.MKTP.KD": {"name": "GDP (constant 2015 USD)", "unit": "USD"},
    "NY.GDP.PCAP.CD": {"name": "GDP per Capita", "unit": "USD"},
    "FP.CPI.TOTL.ZG": {"name": "Inflation (CPI)", "unit": "% annual"},
    "SL.UEM.TOTL.ZS": {"name": "Unemployment Rate", "unit": "% of labor force"},
    "BN.CAB.XOKA.GD.ZS": {"name": "Current Account Balance", "unit": "% of GDP"},
    "BX.KLT.DINV.WD.GD.ZS": {"name": "FDI Inflows", "unit": "% of GDP"},
    "GC.DOD.TOTL.GD.ZS": {"name": "Government Debt", "unit": "% of GDP"},
    "NE.EXP.GNFS.ZS": {"name": "Exports", "unit": "% of GDP"},
    "NE.IMP.GNFS.ZS": {"name": "Imports", "unit": "% of GDP"},
    "NE.TRD.GNFS.ZS": {"name": "Trade Openness", "unit": "% of GDP"},
    "SP.POP.TOTL": {"name": "Population", "unit": "total"},
    "SI.POV.DDAY": {"name": "Poverty ($2.15/day)", "unit": "% of population"},
    "SP.DYN.LE00.IN": {"name": "Life Expectancy", "unit": "years"},
    "SI.POV.GINI": {"name": "Gini Index", "unit": "0-100"},
}

# Regional codes
REGIONAL_CODES = {
    "sub-saharan africa": "SSF",
    "middle east & north africa": "MEA",
    "mena": "MEA",
    "latin america": "LCN",
    "europe & central asia": "ECS",
    "east asia": "EAS",
    "south asia": "SAS",
    "oecd": "OED",
    "world": "WLD",
    "low income": "LIC",
    "middle income": "MIC",
    "high income": "HIC",
}


class WorldBankClient:
    """Client for World Bank API."""

    def __init__(self):
        self.base_url = settings.worldbank_base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_data(
        self,
        countries: list[str],
        indicator: str,
        start_year: int,
        end_year: int,
    ) -> dict:
        """
        Fetch data from World Bank API.

        Args:
            countries: List of ISO3 country codes
            indicator: World Bank indicator code
            start_year: Start year for data range
            end_year: End year for data range

        Returns:
            Formatted data with indicator metadata
        """
        country_str = ";".join(countries)
        url = f"{self.base_url}/country/{country_str}/indicator/{indicator}"

        params = {
            "format": "json",
            "date": f"{start_year}:{end_year}",
            "per_page": 1000,
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to fetch data from World Bank: {str(e)}")

        # World Bank returns [metadata, data] or just [metadata]
        if not data or len(data) < 2 or not data[1]:
            return {
                "data": [],
                "indicator": INDICATORS.get(indicator, {"name": indicator, "unit": ""}),
                "countries": [{"iso3": c} for c in countries],
                "startYear": start_year,
                "endYear": end_year,
                "source": "Source: World Bank Open Data. License: CC BY 4.0",
                "fetchedAt": datetime.now().isoformat(),
            }

        raw_data = data[1]

        # Transform to our format
        data_points = []
        country_info = {}

        for item in raw_data:
            country_code = item.get("countryiso3code", item.get("country", {}).get("id", ""))
            country_name = item.get("country", {}).get("value", country_code)

            if country_code not in country_info:
                country_info[country_code] = {"name": country_name, "iso3": country_code}

            data_points.append({
                "country": country_name,
                "countryCode": country_code,
                "indicator": item.get("indicator", {}).get("value", indicator),
                "indicatorCode": indicator,
                "year": int(item.get("date", 0)),
                "value": item.get("value"),
            })

        # Sort by year
        data_points.sort(key=lambda x: (x["countryCode"], x["year"]))

        return {
            "data": data_points,
            "indicator": INDICATORS.get(indicator, {"name": indicator, "unit": "", "code": indicator}),
            "countries": list(country_info.values()),
            "startYear": start_year,
            "endYear": end_year,
            "source": "Source: World Bank Open Data. License: CC BY 4.0",
            "fetchedAt": datetime.now().isoformat(),
        }

    async def fetch_regional_average(
        self,
        region_code: str,
        indicator: str,
        start_year: int,
        end_year: int,
    ) -> dict:
        """Fetch regional average data."""
        return await self.fetch_data(
            countries=[region_code],
            indicator=indicator,
            start_year=start_year,
            end_year=end_year,
        )

    async def get_country_region(self, country_code: str) -> Optional[str]:
        """Get the region code for a country."""
        url = f"{self.base_url}/country/{country_code}"
        params = {"format": "json"}

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data and len(data) > 1 and data[1]:
                country_data = data[1][0]
                region = country_data.get("region", {})
                region_id = region.get("id", "")

                # Map to aggregate codes
                region_mapping = {
                    "SSF": "SSF",  # Sub-Saharan Africa
                    "MEA": "MEA",  # Middle East & North Africa
                    "LCN": "LCN",  # Latin America
                    "ECS": "ECS",  # Europe & Central Asia
                    "EAS": "EAS",  # East Asia & Pacific
                    "SAS": "SAS",  # South Asia
                    "NAC": "NAC",  # North America
                }
                return region_mapping.get(region_id)

        except httpx.HTTPError:
            pass

        return None

    async def get_country_info(self, country_code: str) -> dict:
        """Get country metadata."""
        url = f"{self.base_url}/country/{country_code}"
        params = {"format": "json"}

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data and len(data) > 1 and data[1]:
                country_data = data[1][0]
                return {
                    "iso3": country_data.get("id"),
                    "iso2": country_data.get("iso2Code"),
                    "name": country_data.get("name"),
                    "region": country_data.get("region", {}).get("value"),
                    "incomeLevel": country_data.get("incomeLevel", {}).get("value"),
                    "capitalCity": country_data.get("capitalCity"),
                }

        except httpx.HTTPError:
            pass

        return {"iso3": country_code, "name": country_code}

    async def search_countries(self, query: str, limit: int = 10) -> list[dict]:
        """Search for countries by name."""
        url = f"{self.base_url}/country"
        params = {"format": "json", "per_page": 300}

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data and len(data) > 1 and data[1]:
                query_lower = query.lower()
                matches = []

                for country in data[1]:
                    name = country.get("name", "").lower()
                    if query_lower in name:
                        matches.append({
                            "iso3": country.get("id"),
                            "iso2": country.get("iso2Code"),
                            "name": country.get("name"),
                        })

                return matches[:limit]

        except httpx.HTTPError:
            pass

        return []

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
