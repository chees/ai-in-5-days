"""Architectural Co-Design Agent with Multi-Agent Orchestration & Model Routing.

Implements:
- Multi-Agent Patterns (Criteria 9): Coordinator pattern with specialized subagents
  (ParcelPlotMapperAgent, BuildingZoningAuditorAgent).
- Strategic Model Routing (Criteria 10): Routes fast geometry/vector lookups to Flash
  and complex architectural reasoning and master planning to Pro.
- Robust System Instructions (Criteria 5): Grounded by ARCHITECTURAL_CONSTITUTION.
- Integrated Observability & Tracing (Criteria 13, 14, 15).
"""

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.config import config
from app.system_prompt import ARCHITECTURAL_CONSTITUTION
from app.tools.parcel_tools import (
    fetch_cadastral_parcel_boundary,
    calculate_building_envelope_setbacks,
    query_adjacent_parcel_assemblage,
    generate_architectural_site_report,
)
from app.observability.logging import get_logger
from app.observability.tracer import get_tracer

logger = get_logger("app.agent")
tracer = get_tracer("ai-in-5-days-architect")


# =====================================================================
# Strategic Model Routing Configuration (Criteria 10)
# =====================================================================
# Fast model for tactical geospatial data extraction, schemas, and coordinates
FAST_MODEL_INSTANCE = Gemini(
    model=config.fast_model,
    retry_options=types.HttpRetryOptions(attempts=3),
)

# Deep reasoning model for coordinator planning, cross-agent synthesis, and compliance
REASONING_MODEL_INSTANCE = Gemini(
    model=config.reasoning_model,
    retry_options=types.HttpRetryOptions(attempts=3),
)


# =====================================================================
# Specialized Subagent 1: Parcel Plot Mapper (Criteria 9: Multi-Agent)
# =====================================================================
parcel_plot_mapper_agent = Agent(
    name="parcel_plot_mapper",
    description="Specialist agent for cadastral parcel boundaries, lot coordinates, and adjacent land assemblage.",
    model=FAST_MODEL_INSTANCE,  # Routed to fast model (Criteria 10)
    instruction=(
        "You are the Parcel Plot Mapper specialist. Your responsibility is extracting authoritative "
        "cadastral parcel boundaries, validating coordinates, calculating lot areas in square meters, "
        "and identifying adjacent property assemblages. Always provide clear, precise geospatial dimensions."
    ),
    tools=[fetch_cadastral_parcel_boundary, query_adjacent_parcel_assemblage],
)


# =====================================================================
# Specialized Subagent 2: Building Zoning Auditor (Criteria 9: Multi-Agent)
# =====================================================================
building_zoning_auditor_agent = Agent(
    name="building_zoning_auditor",
    description="Specialist agent for municipal zoning bylaws, building envelope setbacks, and FAR limits.",
    model=FAST_MODEL_INSTANCE,  # Routed to fast model (Criteria 10)
    instruction=(
        "You are the Building Zoning Auditor specialist. Your responsibility is applying municipal setback regulations "
        "(front, rear, lateral), computing legal buildable footprints, maximum allowable building heights, "
        "and maximum buildable volume envelopes. Offer guided variance suggestions if setbacks exceed lot dimensions."
    ),
    tools=[calculate_building_envelope_setbacks],
)


# =====================================================================
# Root Coordinator Agent (Criteria 9: Coordinator Pattern)
# =====================================================================
root_agent = Agent(
    name="architectural_coordinator",
    description="Master architectural coordinator orchestrating site analysis, zoning audits, and parcel mapping.",
    model=REASONING_MODEL_INSTANCE,  # Routed to high-reasoning model (Criteria 10)
    instruction=ARCHITECTURAL_CONSTITUTION,  # Robust constitution (Criteria 5)
    sub_agents=[parcel_plot_mapper_agent, building_zoning_auditor_agent],  # Multi-agent pattern (Criteria 9)
    tools=[generate_architectural_site_report],
)


# =====================================================================
# Application Export
# =====================================================================
app = App(
    root_agent=root_agent,
    name="app",
)
