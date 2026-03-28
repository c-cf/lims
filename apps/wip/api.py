"""Django Ninja routers for WIP, Dispatch, and Automation endpoints."""

from django.db import IntegrityError, models, transaction
from django.db.models import Prefetch
from django.http import HttpRequest
from django.utils import timezone
from ninja import Query, Router

from api.schemas import ErrorOut
from apps.accounts.auth import JWTAuth
from apps.accounts.permissions import has_lab_role
from apps.commissions.models import Request, RequestStatus, Sample, SampleStatus
from apps.commissions.state_machine import validate_sample_transition
from apps.equipment.models import Equipment, EquipmentCapability, Recipe
from apps.experiments.models import ExperimentType
from apps.wip.models import WIP, Dispatch, DispatchStatus, ExperimentResult, WIPStatus
from apps.wip.schemas import (
    AutomationResultIn,
    DispatchDetailOut,
    DispatchIn,
    DispatchListOut,
    ExceptionReportIn,
    ExperimentResultIn,
    WIPDetailOut,
    WIPIn,
    WIPListOut,
)
from apps.wip.state_machine import (
    InvalidTransitionError,
    validate_dispatch_transition,
    validate_wip_transition,
)

router = Router(tags=["WIPs"], auth=JWTAuth())
dispatch_router = Router(tags=["Dispatches"], auth=JWTAuth())
automation_router = Router(tags=["Automation"], auth=JWTAuth())


# =============================================================================
# Helpers
# =============================================================================


def _wip_detail_queryset() -> "models.QuerySet[WIP]":
    """Base queryset with all prefetches needed for WIPDetailOut."""
    return WIP.objects.prefetch_related(
        Prefetch(
            "dispatches",
            queryset=Dispatch.objects.select_related(
                "experiment_type", "equipment", "recipe"
            ).order_by("created_at"),
        )
    )


def _dispatch_detail_queryset() -> "models.QuerySet[Dispatch]":
    """Base queryset with all prefetches needed for DispatchDetailOut."""
    return Dispatch.objects.select_related(
        "experiment_type", "equipment", "recipe"
    ).prefetch_related("result")


def _check_all_dispatches_done(wip: WIP) -> bool:
    """Return True if all dispatches for the WIP are in a terminal state.

    PENDING_REDISPATCH is intentionally treated as terminal here: when a
    dispatch is redispatched, the original stays at PENDING_REDISPATCH (a
    historical record) and a new dispatch is created. The WIP can be marked
    complete once the new dispatch (and all others) finish.
    """
    active_statuses = {
        DispatchStatus.PENDING,
        DispatchStatus.DISPATCHED,
        DispatchStatus.RUNNING,
        DispatchStatus.UNLOADED,
        DispatchStatus.RESULT_RECORDED,
    }
    return not wip.dispatches.filter(status__in=active_statuses).exists()


def _complete_sample_and_check_request(sample: Sample) -> None:
    """Mark sample as completed, then auto-complete the request if all samples are done.

    Must be called inside an active transaction.atomic() block, after the
    caller has already acquired a select_for_update lock on the sample row.
    """
    try:
        target = validate_sample_transition(sample.status, "complete")
    except InvalidTransitionError:
        return  # Sample not in a completable state; skip

    sample.status = target
    sample.save()

    # Lock the request row to prevent concurrent auto-completion races.
    req = Request.objects.select_for_update().get(pk=sample.request_id)
    if req.status != RequestStatus.IN_PROGRESS:
        return

    completed_statuses = {
        SampleStatus.COMPLETED,
        SampleStatus.VOIDED,
        SampleStatus.RETURNED,
    }
    total = req.samples.count()
    terminal_count = req.samples.filter(status__in=completed_statuses).count()

    if total > 0 and terminal_count == total:
        req.status = RequestStatus.COMPLETED
        req.save()


# =============================================================================
# WIP endpoints
# =============================================================================


@router.get("/", response={200: list[WIPListOut], 403: ErrorOut})
def list_wips(
    request: HttpRequest,
    status: WIPStatus | None = Query(None),  # noqa: B008
):
    """List WIPs. Lab staff and managers only."""
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    qs = WIP.objects.order_by("-created_at")
    if status:
        qs = qs.filter(status=status)

    return 200, list(qs)


@router.post(
    "/",
    response={
        201: WIPDetailOut,
        400: ErrorOut,
        403: ErrorOut,
        404: ErrorOut,
        409: ErrorOut,
    },
)
def create_wip(request: HttpRequest, payload: WIPIn):
    """Create a WIP for a sample. Lab staff only."""
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    try:
        sample = Sample.objects.get(pk=payload.sample_id)
    except Sample.DoesNotExist:
        return 404, {"detail": "Sample not found"}

    try:
        with transaction.atomic():
            wip = WIP.objects.create(
                sample=sample,
                note=payload.note,
                created_by=request.auth,
            )
    except IntegrityError:
        return 409, {"detail": "A WIP already exists for this sample"}

    wip = _wip_detail_queryset().get(pk=wip.pk)
    return 201, WIPDetailOut.from_wip(wip)


@router.get("/{wip_id}/", response={200: WIPDetailOut, 403: ErrorOut, 404: ErrorOut})
def get_wip(request: HttpRequest, wip_id: int):
    """Get WIP detail with dispatches. Lab staff and managers only."""
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    try:
        wip = _wip_detail_queryset().get(pk=wip_id)
    except WIP.DoesNotExist:
        return 404, {"detail": "Not found"}

    return 200, WIPDetailOut.from_wip(wip)


@router.post(
    "/{wip_id}/dispatches/",
    response={201: WIPDetailOut, 400: ErrorOut, 403: ErrorOut, 404: ErrorOut},
)
def create_dispatch(request: HttpRequest, wip_id: int, payload: DispatchIn):
    """Create a dispatch for a WIP. Validates equipment capability and recipe.

    Automatically transitions WIP to in_progress on first dispatch.
    """
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    # Validate foreign keys before acquiring the WIP lock.
    try:
        experiment_type = ExperimentType.objects.get(
            pk=payload.experiment_type_id, is_active=True
        )
    except ExperimentType.DoesNotExist:
        return 400, {"detail": "Experiment type not found or inactive"}

    try:
        equipment = Equipment.objects.get(pk=payload.equipment_id)
    except Equipment.DoesNotExist:
        return 400, {"detail": "Equipment not found"}

    try:
        recipe = Recipe.objects.get(pk=payload.recipe_id, equipment=equipment)
    except Recipe.DoesNotExist:
        return 400, {
            "detail": "Recipe not found or does not belong to the given equipment"
        }

    if not EquipmentCapability.objects.filter(
        equipment=equipment, experiment_type=experiment_type
    ).exists():
        return 400, {"detail": "Equipment does not support this experiment type"}

    with transaction.atomic():
        try:
            wip = WIP.objects.select_for_update().get(pk=wip_id)
        except WIP.DoesNotExist:
            return 404, {"detail": "Not found"}

        Dispatch.objects.create(
            wip=wip,
            experiment_type=experiment_type,
            equipment=equipment,
            recipe=recipe,
            note=payload.note,
            created_by=request.auth,
        )

        # Auto-transition WIP to in_progress on first dispatch.
        if wip.status == WIPStatus.CREATED:
            wip.status = WIPStatus.IN_PROGRESS
            wip.save()

    wip = _wip_detail_queryset().get(pk=wip_id)
    return 201, WIPDetailOut.from_wip(wip)


@router.post(
    "/{wip_id}/complete/",
    response={200: WIPDetailOut, 400: ErrorOut, 403: ErrorOut, 404: ErrorOut},
)
def complete_wip(request: HttpRequest, wip_id: int):
    """Complete a WIP. Requires all dispatches to be in terminal state.

    Auto-completes the sample and checks if the parent request is done.
    """
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    with transaction.atomic():
        try:
            wip = WIP.objects.select_for_update().get(pk=wip_id)
        except WIP.DoesNotExist:
            return 404, {"detail": "Not found"}

        if not _check_all_dispatches_done(wip):
            return 400, {
                "detail": "All dispatches must be completed or aborted before completing the WIP"
            }

        try:
            target = validate_wip_transition(wip.status, "complete")
        except InvalidTransitionError as e:
            return 400, {"detail": str(e)}

        wip.status = target
        wip.completed_at = timezone.now()
        wip.save()

        # Auto-complete the sample and propagate to the request if needed.
        sample = Sample.objects.select_for_update().get(pk=wip.sample_id)
        _complete_sample_and_check_request(sample)

    wip = _wip_detail_queryset().get(pk=wip_id)
    return 200, WIPDetailOut.from_wip(wip)


@router.post(
    "/{wip_id}/abort/",
    response={200: WIPDetailOut, 400: ErrorOut, 403: ErrorOut, 404: ErrorOut},
)
def abort_wip(request: HttpRequest, wip_id: int):
    """Abort a WIP. Marks the associated sample as processing_exception."""
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    with transaction.atomic():
        try:
            wip = WIP.objects.select_for_update().get(pk=wip_id)
        except WIP.DoesNotExist:
            return 404, {"detail": "Not found"}

        try:
            target = validate_wip_transition(wip.status, "abort")
        except InvalidTransitionError as e:
            return 400, {"detail": str(e)}

        wip.status = target
        wip.save()

        # Mark sample as processing_exception; skip if already in a terminal state.
        sample = Sample.objects.select_for_update().get(pk=wip.sample_id)
        try:
            sample_target = validate_sample_transition(
                sample.status, "processing_exception"
            )
            sample.status = sample_target
            sample.save()
        except InvalidTransitionError:
            pass

    wip = _wip_detail_queryset().get(pk=wip_id)
    return 200, WIPDetailOut.from_wip(wip)


# =============================================================================
# Dispatch endpoints
# =============================================================================


@dispatch_router.get("/", response={200: list[DispatchListOut], 403: ErrorOut})
def list_dispatches(
    request: HttpRequest,
    status: DispatchStatus | None = Query(None),  # noqa: B008
    wip_id: int | None = Query(None),
    equipment_id: int | None = Query(None),
):
    """List dispatches with optional filters. Lab staff and managers only."""
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    qs = Dispatch.objects.order_by("-created_at")
    if status:
        qs = qs.filter(status=status)
    if wip_id:
        qs = qs.filter(wip_id=wip_id)
    if equipment_id:
        qs = qs.filter(equipment_id=equipment_id)

    return 200, list(qs)


@dispatch_router.get(
    "/{dispatch_id}/", response={200: DispatchDetailOut, 403: ErrorOut, 404: ErrorOut}
)
def get_dispatch(request: HttpRequest, dispatch_id: int):
    """Get dispatch detail. Lab staff and managers only."""
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    try:
        dispatch = _dispatch_detail_queryset().get(pk=dispatch_id)
    except Dispatch.DoesNotExist:
        return 404, {"detail": "Not found"}

    return 200, DispatchDetailOut.from_dispatch(dispatch)


@dispatch_router.post(
    "/{dispatch_id}/start/",
    response={200: DispatchDetailOut, 400: ErrorOut, 403: ErrorOut, 404: ErrorOut},
)
def start_dispatch(request: HttpRequest, dispatch_id: int):
    """Start a dispatch (pending/dispatched → running). Lab staff only."""
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    with transaction.atomic():
        try:
            dispatch = Dispatch.objects.select_for_update().get(pk=dispatch_id)
        except Dispatch.DoesNotExist:
            return 404, {"detail": "Not found"}

        # If PENDING, run the "dispatch" transition first, then "start".
        if dispatch.status == DispatchStatus.PENDING:
            try:
                validate_dispatch_transition(dispatch.status, "dispatch")
            except InvalidTransitionError as e:
                return 400, {"detail": str(e)}
            dispatch.status = DispatchStatus.DISPATCHED
            dispatch.dispatched_at = timezone.now()

        try:
            target = validate_dispatch_transition(dispatch.status, "start")
        except InvalidTransitionError as e:
            return 400, {"detail": str(e)}

        dispatch.status = target
        dispatch.save()

    dispatch = _dispatch_detail_queryset().get(pk=dispatch_id)
    return 200, DispatchDetailOut.from_dispatch(dispatch)


@dispatch_router.post(
    "/{dispatch_id}/unload/",
    response={200: DispatchDetailOut, 400: ErrorOut, 403: ErrorOut, 404: ErrorOut},
)
def unload_dispatch(request: HttpRequest, dispatch_id: int):
    """Unload a dispatch (dispatched/running → unloaded). Lab staff only."""
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    with transaction.atomic():
        try:
            dispatch = Dispatch.objects.select_for_update().get(pk=dispatch_id)
        except Dispatch.DoesNotExist:
            return 404, {"detail": "Not found"}

        try:
            target = validate_dispatch_transition(dispatch.status, "unload")
        except InvalidTransitionError as e:
            return 400, {"detail": str(e)}

        dispatch.status = target
        dispatch.save()

    dispatch = _dispatch_detail_queryset().get(pk=dispatch_id)
    return 200, DispatchDetailOut.from_dispatch(dispatch)


@dispatch_router.post(
    "/{dispatch_id}/record-result/",
    response={200: DispatchDetailOut, 400: ErrorOut, 403: ErrorOut, 404: ErrorOut},
)
def record_result(request: HttpRequest, dispatch_id: int, payload: ExperimentResultIn):
    """Record result for an unloaded dispatch. Creates ExperimentResult. Lab staff only."""
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    with transaction.atomic():
        try:
            dispatch = Dispatch.objects.select_for_update().get(pk=dispatch_id)
        except Dispatch.DoesNotExist:
            return 404, {"detail": "Not found"}

        try:
            target = validate_dispatch_transition(dispatch.status, "record_result")
        except InvalidTransitionError as e:
            return 400, {"detail": str(e)}

        dispatch.status = target
        if payload.note:
            dispatch.note = f"{dispatch.note}\n{payload.note}".strip()
        dispatch.save()

        ExperimentResult.objects.create(
            dispatch=dispatch,
            summary=payload.summary,
            verdict=payload.verdict,
            data=payload.data,
            data_source=ExperimentResult.DataSource.MANUAL,
            recorded_by=request.auth,
        )

    dispatch = _dispatch_detail_queryset().get(pk=dispatch_id)
    return 200, DispatchDetailOut.from_dispatch(dispatch)


@dispatch_router.post(
    "/{dispatch_id}/complete/",
    response={200: DispatchDetailOut, 400: ErrorOut, 403: ErrorOut, 404: ErrorOut},
)
def complete_dispatch(request: HttpRequest, dispatch_id: int):
    """Complete a result_recorded dispatch. Lab staff only."""
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    with transaction.atomic():
        try:
            dispatch = Dispatch.objects.select_for_update().get(pk=dispatch_id)
        except Dispatch.DoesNotExist:
            return 404, {"detail": "Not found"}

        try:
            target = validate_dispatch_transition(dispatch.status, "complete")
        except InvalidTransitionError as e:
            return 400, {"detail": str(e)}

        dispatch.status = target
        dispatch.completed_at = timezone.now()
        dispatch.save()

    dispatch = _dispatch_detail_queryset().get(pk=dispatch_id)
    return 200, DispatchDetailOut.from_dispatch(dispatch)


@dispatch_router.post(
    "/{dispatch_id}/report-exception/",
    response={200: DispatchDetailOut, 400: ErrorOut, 403: ErrorOut, 404: ErrorOut},
)
def report_exception(
    request: HttpRequest,
    dispatch_id: int,
    payload: ExceptionReportIn = ExceptionReportIn(),  # noqa: B008
):
    """Report an execution exception. Lab staff only."""
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    with transaction.atomic():
        try:
            dispatch = Dispatch.objects.select_for_update().get(pk=dispatch_id)
        except Dispatch.DoesNotExist:
            return 404, {"detail": "Not found"}

        try:
            target = validate_dispatch_transition(dispatch.status, "report_exception")
        except InvalidTransitionError as e:
            return 400, {"detail": str(e)}

        dispatch.status = target
        if payload.note:
            dispatch.note = f"{dispatch.note}\n[Exception] {payload.note}".strip()
        dispatch.save()

    dispatch = _dispatch_detail_queryset().get(pk=dispatch_id)
    return 200, DispatchDetailOut.from_dispatch(dispatch)


@dispatch_router.post(
    "/{dispatch_id}/redispatch/",
    response={200: DispatchDetailOut, 400: ErrorOut, 403: ErrorOut, 404: ErrorOut},
)
def redispatch(request: HttpRequest, dispatch_id: int):
    """Redispatch an exception dispatch. Creates a new PENDING dispatch. Lab staff only."""
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    with transaction.atomic():
        try:
            dispatch = (
                Dispatch.objects.select_for_update()
                .select_related("wip")
                .get(pk=dispatch_id)
            )
        except Dispatch.DoesNotExist:
            return 404, {"detail": "Not found"}

        try:
            target = validate_dispatch_transition(dispatch.status, "redispatch")
        except InvalidTransitionError as e:
            return 400, {"detail": str(e)}

        dispatch.status = target
        dispatch.save()

        # Create a new dispatch at PENDING with the same equipment/experiment parameters.
        Dispatch.objects.create(
            wip=dispatch.wip,
            experiment_type=dispatch.experiment_type,
            equipment=dispatch.equipment,
            recipe=dispatch.recipe,
            created_by=request.auth,
        )

    dispatch = _dispatch_detail_queryset().get(pk=dispatch_id)
    return 200, DispatchDetailOut.from_dispatch(dispatch)


@dispatch_router.post(
    "/{dispatch_id}/abort/",
    response={200: DispatchDetailOut, 400: ErrorOut, 403: ErrorOut, 404: ErrorOut},
)
def abort_dispatch(request: HttpRequest, dispatch_id: int):
    """Abort a dispatch. Lab staff and managers allowed."""
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    with transaction.atomic():
        try:
            dispatch = Dispatch.objects.select_for_update().get(pk=dispatch_id)
        except Dispatch.DoesNotExist:
            return 404, {"detail": "Not found"}

        try:
            target = validate_dispatch_transition(dispatch.status, "abort")
        except InvalidTransitionError as e:
            return 400, {"detail": str(e)}

        dispatch.status = target
        dispatch.save()

    dispatch = _dispatch_detail_queryset().get(pk=dispatch_id)
    return 200, DispatchDetailOut.from_dispatch(dispatch)


# =============================================================================
# Automation endpoints
# =============================================================================


@automation_router.post(
    "/equipment-result/",
    response={200: DispatchDetailOut, 400: ErrorOut, 403: ErrorOut, 404: ErrorOut},
)
def submit_equipment_result(request: HttpRequest, payload: AutomationResultIn):
    """Automated equipment result submission. Completes dispatch and creates result.

    Accepts dispatch in DISPATCHED or RUNNING state. Runs the full state
    machine chain: unload → record_result → complete.
    """
    if not has_lab_role(request):
        return 403, {"detail": "Permission denied"}

    with transaction.atomic():
        try:
            dispatch = Dispatch.objects.select_for_update().get(pk=payload.dispatch_id)
        except Dispatch.DoesNotExist:
            return 404, {"detail": "Dispatch not found"}

        # Run state machine chain: (dispatched|running) → unloaded → result_recorded → completed.
        for action in ("unload", "record_result", "complete"):
            try:
                target = validate_dispatch_transition(dispatch.status, action)
            except InvalidTransitionError as e:
                return 400, {"detail": str(e)}
            dispatch.status = target

        dispatch.completed_at = timezone.now()
        dispatch.save()

        ExperimentResult.objects.create(
            dispatch=dispatch,
            summary=payload.summary,
            verdict=payload.verdict,
            data=payload.data,
            data_source=ExperimentResult.DataSource.AUTOMATED,
        )

    dispatch = _dispatch_detail_queryset().get(pk=payload.dispatch_id)
    return 200, DispatchDetailOut.from_dispatch(dispatch)
