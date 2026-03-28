"""Ninja schemas for the wip app."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from ninja import Field, Schema

if TYPE_CHECKING:
    from apps.wip.models import WIP, Dispatch


# --- Nested output schemas ---


class DispatchBriefOut(Schema):
    """Brief dispatch info nested in WIP responses."""

    id: int
    experiment_type_id: int
    experiment_type_name: str
    equipment_id: int
    equipment_name: str
    recipe_id: int
    recipe_name: str
    status: str
    dispatched_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class ExperimentResultOut(Schema):
    """Experiment result details nested in dispatch responses."""

    id: int
    summary: str
    verdict: str
    data: dict[str, Any]
    data_source: str
    created_at: datetime


# --- WIP input schemas ---


class WIPIn(Schema):
    """Input schema for creating a WIP."""

    sample_id: int
    note: str = ""


# --- Dispatch input schemas ---


class DispatchIn(Schema):
    """Input schema for creating a dispatch."""

    experiment_type_id: int
    equipment_id: int
    recipe_id: int
    note: str = ""


class ExperimentResultIn(Schema):
    """Input schema for recording an experiment result."""

    summary: str = Field(..., min_length=1)
    verdict: str = Field(..., pattern="^(pass|fail)$")
    data: dict[str, Any] = {}
    note: str = ""


class ExceptionReportIn(Schema):
    """Input schema for reporting a dispatch exception."""

    note: str = ""


class AutomationResultIn(Schema):
    """Input schema for automated equipment result submission."""

    dispatch_id: int
    summary: str = Field(..., min_length=1)
    verdict: str = Field(..., pattern="^(pass|fail)$")
    data: dict[str, Any] = {}


# --- WIP output schemas ---


class WIPListOut(Schema):
    """Output schema for WIP list responses."""

    id: int
    sample_id: int
    status: str
    note: str
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class WIPDetailOut(Schema):
    """Output schema for WIP detail responses."""

    id: int
    sample_id: int
    status: str
    note: str
    dispatches: list[DispatchBriefOut]
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_wip(wip: WIP) -> dict:
        """Build a dict from a WIP instance with nested dispatches."""
        dispatches = []
        for d in wip.dispatches.all():
            dispatches.append(
                {
                    "id": d.pk,
                    "experiment_type_id": d.experiment_type_id,
                    "experiment_type_name": d.experiment_type.name,
                    "equipment_id": d.equipment_id,
                    "equipment_name": d.equipment.name,
                    "recipe_id": d.recipe_id,
                    "recipe_name": d.recipe.name,
                    "status": d.status,
                    "dispatched_at": d.dispatched_at,
                    "completed_at": d.completed_at,
                    "created_at": d.created_at,
                }
            )
        return {
            "id": wip.pk,
            "sample_id": wip.sample_id,
            "status": wip.status,
            "note": wip.note,
            "dispatches": dispatches,
            "completed_at": wip.completed_at,
            "created_at": wip.created_at,
            "updated_at": wip.updated_at,
        }


# --- Dispatch output schemas ---


class DispatchDetailOut(Schema):
    """Output schema for dispatch detail responses."""

    id: int
    wip_id: int
    experiment_type_id: int
    experiment_type_name: str
    equipment_id: int
    equipment_name: str
    recipe_id: int
    recipe_name: str
    status: str
    note: str
    dispatched_at: datetime | None
    completed_at: datetime | None
    result: ExperimentResultOut | None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_dispatch(dispatch: Dispatch) -> dict:
        """Build a dict from a Dispatch instance."""
        result = None
        if hasattr(dispatch, "result"):
            r = dispatch.result
            result = {
                "id": r.pk,
                "summary": r.summary,
                "verdict": r.verdict,
                "data": r.data,
                "data_source": r.data_source,
                "created_at": r.created_at,
            }
        return {
            "id": dispatch.pk,
            "wip_id": dispatch.wip_id,
            "experiment_type_id": dispatch.experiment_type_id,
            "experiment_type_name": dispatch.experiment_type.name,
            "equipment_id": dispatch.equipment_id,
            "equipment_name": dispatch.equipment.name,
            "recipe_id": dispatch.recipe_id,
            "recipe_name": dispatch.recipe.name,
            "status": dispatch.status,
            "note": dispatch.note,
            "dispatched_at": dispatch.dispatched_at,
            "completed_at": dispatch.completed_at,
            "result": result,
            "created_at": dispatch.created_at,
            "updated_at": dispatch.updated_at,
        }


class DispatchListOut(Schema):
    """Output schema for dispatch list responses."""

    id: int
    wip_id: int
    experiment_type_id: int
    equipment_id: int
    recipe_id: int
    status: str
    dispatched_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
