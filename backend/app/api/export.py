"""Export API endpoints for generating reports and downloads."""

from typing import Optional, Literal
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
import csv
import json

router = APIRouter()


class ExportRequest(BaseModel):
    """Request model for export endpoint."""

    session_id: Optional[str] = None
    data: Optional[dict] = None
    format: Literal["csv", "json", "markdown", "pdf"] = "csv"
    include_narrative: bool = True
    include_sources: bool = True


@router.post("/data")
async def export_data(request: ExportRequest):
    """
    Export data in various formats.

    Supports:
    - CSV: Raw data export
    - JSON: Full data with metadata
    - Markdown: Formatted report
    - PDF: Print-ready document (TODO)
    """
    if not request.data:
        raise HTTPException(status_code=400, detail="No data provided for export")

    if request.format == "csv":
        return export_csv(request.data)
    elif request.format == "json":
        return export_json(request.data)
    elif request.format == "markdown":
        return export_markdown(request.data, request.include_narrative)
    else:
        raise HTTPException(
            status_code=400, detail=f"Format {request.format} not yet supported"
        )


def export_csv(data: dict) -> StreamingResponse:
    """Export data as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Extract data points
    points = data.get("data", [])
    if not points:
        raise HTTPException(status_code=400, detail="No data points to export")

    # Write header
    headers = ["Country", "Year", "Indicator", "Value", "Unit"]
    writer.writerow(headers)

    # Write data
    indicator = data.get("indicator", {})
    for point in points:
        writer.writerow(
            [
                point.get("country", ""),
                point.get("year", ""),
                indicator.get("name", ""),
                point.get("value", ""),
                indicator.get("unit", ""),
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=econchat_export_{data.get('indicator', {}).get('code', 'data')}.csv"
        },
    )


def export_json(data: dict) -> dict:
    """Export data as JSON with full metadata."""
    return {
        "exported_at": "2024-01-01T00:00:00Z",  # TODO: use actual timestamp
        "format_version": "1.0",
        "data": data,
    }


def export_markdown(data: dict, include_narrative: bool = True) -> StreamingResponse:
    """Export data as formatted Markdown report."""
    indicator = data.get("indicator", {})
    countries = data.get("countries", [])
    points = data.get("data", [])
    narrative = data.get("narrative", {})

    md_lines = []

    # Title
    md_lines.append(f"# {indicator.get('name', 'Economic Data Report')}")
    md_lines.append("")

    # Summary
    if include_narrative and narrative:
        md_lines.append("## Summary")
        md_lines.append("")
        if narrative.get("summary"):
            md_lines.append(narrative["summary"])
        if narrative.get("trendDescription"):
            md_lines.append("")
            md_lines.append(narrative["trendDescription"])
        if narrative.get("peerComparison"):
            md_lines.append("")
            md_lines.append(narrative["peerComparison"])
        md_lines.append("")

    # Countries
    if countries:
        country_names = [c.get("name", "") for c in countries]
        md_lines.append(f"**Countries:** {', '.join(country_names)}")
        md_lines.append("")

    # Data table
    md_lines.append("## Data")
    md_lines.append("")
    md_lines.append("| Country | Year | Value |")
    md_lines.append("|---------|------|-------|")

    for point in points:
        value = point.get("value")
        value_str = f"{value:.2f}" if value is not None else "N/A"
        md_lines.append(
            f"| {point.get('country', '')} | {point.get('year', '')} | {value_str} |"
        )

    md_lines.append("")

    # Source
    md_lines.append("---")
    md_lines.append("")
    md_lines.append(f"*Source: {data.get('source', 'World Bank Open Data')}*")

    content = "\n".join(md_lines)

    return StreamingResponse(
        iter([content]),
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename=econchat_report_{indicator.get('code', 'data')}.md"
        },
    )


@router.post("/report")
async def generate_report(
    session_id: str,
    format: Literal["brief", "full", "executive"] = "brief",
):
    """
    Generate a comprehensive report from a session.

    Report types:
    - brief: 1-2 page summary with key findings
    - full: Complete analysis with all data and visualizations
    - executive: C-suite ready summary with key metrics
    """
    # TODO: Implement report generation with Claude
    return {
        "status": "generating",
        "session_id": session_id,
        "format": format,
        "message": "Report generation will be implemented with Claude integration",
    }
