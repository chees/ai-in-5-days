"""Unit tests for Parcel Plot Tools (Criteria 1, 2, 3, 4)."""

import pytest
from app.tools.parcel_tools import (
    ParcelQueryInput,
    ParcelBoundaryOutput,
    SetbackCalculationInput,
    SetbackEnvelopeOutput,
    AdjacentAssemblageInput,
    AssemblageOutput,
    fetch_cadastral_parcel_boundary,
    calculate_building_envelope_setbacks,
    query_adjacent_parcel_assemblage,
    generate_architectural_site_report,
)


def test_tool_docstrings_present():
    """Criteria 1: Comprehensive Tool Docstrings."""
    tools = [
        fetch_cadastral_parcel_boundary,
        calculate_building_envelope_setbacks,
        query_adjacent_parcel_assemblage,
        generate_architectural_site_report,
    ]
    for t in tools:
        assert t.__doc__ is not None, f"Tool {t.__name__} missing docstring"
        assert "Args:" in t.__doc__, f"Tool {t.__name__} missing Args documentation"
        assert "Returns:" in t.__doc__, f"Tool {t.__name__} missing Returns documentation"


def test_descriptive_tool_naming():
    """Criteria 2: Descriptive Naming."""
    # Tool names must be specific and not generic
    assert fetch_cadastral_parcel_boundary.__name__ == "fetch_cadastral_parcel_boundary"
    assert calculate_building_envelope_setbacks.__name__ == "calculate_building_envelope_setbacks"
    assert query_adjacent_parcel_assemblage.__name__ == "query_adjacent_parcel_assemblage"
    assert generate_architectural_site_report.__name__ == "generate_architectural_site_report"


def test_explicit_json_schemas():
    """Criteria 3: Explicit JSON Schemas via Pydantic."""
    query = ParcelQueryInput(latitude=41.505972, longitude=2.346806, cadastral_reference="5653214DF4955S")
    assert query.latitude == 41.505972
    schema = ParcelQueryInput.model_json_schema()
    assert "properties" in schema
    assert "latitude" in schema["properties"]
    assert "longitude" in schema["properties"]

    out_schema = ParcelBoundaryOutput.model_json_schema()
    assert "area_sqm" in out_schema["properties"]


def test_guided_error_handling_invalid_latitude():
    """Criteria 4: Guided Error Handling on invalid input."""
    # Out-of-bounds latitude should return guided recovery advice, NOT crash
    result = fetch_cadastral_parcel_boundary(latitude=999.0, longitude=2.34)
    assert result["success"] is False
    assert "Guided Recovery" in result["error_recovery_hint"]
    assert "[-90.0, 90.0]" in result["error_recovery_hint"]


def test_guided_error_handling_insufficient_vertices():
    """Criteria 4: Guided Error Handling for polygon calculation."""
    result = calculate_building_envelope_setbacks(
        front_setback_meters=5.0,
        rear_setback_meters=3.0,
        side_setback_meters=3.0,
        max_height_meters=12.0,
        vertices=[(0.0, 0.0), (1.0, 1.0)],  # Only 2 vertices, need >= 3
    )
    assert result["success"] is False
    assert "Guided Recovery" in result["error_recovery_hint"]
    assert "at least 3 points" in result["error_recovery_hint"]


def test_valid_parcel_boundary_retrieval():
    """Test successful cadastral lookup for benchmark site."""
    result = fetch_cadastral_parcel_boundary(latitude=41.505972, longitude=2.346806)
    assert result["success"] is True
    assert result["cadastral_reference"] == "5653214DF4955S"
    assert result["area_sqm"] == 3897.0
    assert len(result["polygon_vertices"]) >= 4


def test_setback_calculation_valid():
    """Test setback and footprint computation."""
    vertices = [(0.0, 0.0), (40.0, 0.0), (40.0, 50.0), (0.0, 50.0)]
    result = calculate_building_envelope_setbacks(
        front_setback_meters=5.0,
        rear_setback_meters=3.0,
        side_setback_meters=3.0,
        max_height_meters=15.0,
        vertices=vertices,
    )
    assert result["success"] is True
    assert result["gross_plot_area_sqm"] == 2000.0
    assert result["buildable_footprint_sqm"] > 0
    assert result["footprint_efficiency_ratio"] > 0
    assert result["max_buildable_volume_cum"] > 0
