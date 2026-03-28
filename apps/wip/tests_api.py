"""API tests for the wip app (WIP, Dispatch, and Automation endpoints)."""

import pytest
from django.test import Client

from apps.accounts.factories import FabUserFactory, LabManagerFactory, LabStaffFactory
from apps.commissions.factories import SampleFactory
from apps.commissions.models import RequestStatus, SampleStatus
from apps.equipment.factories import EquipmentFactory, RecipeFactory
from apps.equipment.models import EquipmentCapability
from apps.experiments.factories import ExperimentTypeFactory
from apps.wip.factories import DispatchFactory, WIPFactory
from apps.wip.models import Dispatch, DispatchStatus, ExperimentResult, WIPStatus


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def auth_headers():
    """Return a factory function that creates JWT Bearer auth headers."""
    from apps.accounts.auth import create_access_token

    def _make_headers(user) -> dict[str, str]:
        token = create_access_token(user.pk)
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    return _make_headers


@pytest.fixture
def fab_user():
    profile = FabUserFactory()
    return profile.user


@pytest.fixture
def lab_staff():
    profile = LabStaffFactory()
    return profile.user


@pytest.fixture
def lab_manager():
    profile = LabManagerFactory()
    return profile.user


@pytest.fixture
def experiment_type():
    return ExperimentTypeFactory()


@pytest.fixture
def equipment(experiment_type):
    """Equipment with capability for the given experiment type."""
    equip = EquipmentFactory()
    EquipmentCapability.objects.create(equipment=equip, experiment_type=experiment_type)
    return equip


@pytest.fixture
def recipe(equipment, experiment_type):
    """Recipe for the given equipment and experiment type."""
    return RecipeFactory(equipment=equipment, experiment_type=experiment_type)


@pytest.fixture
def sample():
    """A received sample (ready for WIP creation)."""
    return SampleFactory(status=SampleStatus.SPLIT)


@pytest.fixture
def wip(sample, lab_staff):
    """A WIP in created state."""
    return WIPFactory(sample=sample, created_by=lab_staff)


@pytest.fixture
def wip_in_progress(lab_staff):
    """A WIP in in_progress state (uses its own sample)."""
    s = SampleFactory(status=SampleStatus.SPLIT)
    return WIPFactory(sample=s, status=WIPStatus.IN_PROGRESS, created_by=lab_staff)


@pytest.fixture
def dispatch(wip_in_progress, experiment_type, equipment, recipe, lab_staff):
    """A dispatch in pending state."""
    return DispatchFactory(
        wip=wip_in_progress,
        experiment_type=experiment_type,
        equipment=equipment,
        recipe=recipe,
        created_by=lab_staff,
    )


@pytest.fixture
def dispatched_dispatch(dispatch):
    """A dispatch in dispatched state."""
    dispatch.status = DispatchStatus.DISPATCHED
    dispatch.save()
    return dispatch


@pytest.fixture
def running_dispatch(dispatch):
    """A dispatch in running state."""
    dispatch.status = DispatchStatus.RUNNING
    dispatch.save()
    return dispatch


@pytest.fixture
def unloaded_dispatch(dispatch):
    """A dispatch in unloaded state."""
    dispatch.status = DispatchStatus.UNLOADED
    dispatch.save()
    return dispatch


@pytest.fixture
def result_recorded_dispatch(dispatch):
    """A dispatch in result_recorded state with an ExperimentResult."""
    dispatch.status = DispatchStatus.RESULT_RECORDED
    dispatch.save()
    ExperimentResult.objects.create(
        dispatch=dispatch,
        summary="Test result",
        verdict=ExperimentResult.Verdict.PASS,
    )
    return dispatch


# =============================================================================
# WIP API Tests
# =============================================================================


@pytest.mark.django_db
class TestWIPList:
    def test_list_wips_as_lab_staff(self, client, auth_headers, lab_staff, wip):
        """Lab staff can list WIPs."""
        resp = client.get("/api/wips/", **auth_headers(lab_staff))
        assert resp.status_code == 200
        data = resp.json()
        assert any(w["id"] == wip.pk for w in data)

    def test_list_wips_as_lab_manager(self, client, auth_headers, lab_manager, wip):
        """Lab manager can list WIPs."""
        resp = client.get("/api/wips/", **auth_headers(lab_manager))
        assert resp.status_code == 200

    def test_list_wips_fab_user_forbidden(self, client, auth_headers, fab_user):
        """Fab user cannot list WIPs."""
        resp = client.get("/api/wips/", **auth_headers(fab_user))
        assert resp.status_code == 403

    def test_list_wips_filter_by_status(
        self, client, auth_headers, lab_staff, wip, wip_in_progress
    ):
        """WIPs can be filtered by status."""
        resp = client.get(
            f"/api/wips/?status={WIPStatus.IN_PROGRESS}", **auth_headers(lab_staff)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(w["status"] == WIPStatus.IN_PROGRESS for w in data)


@pytest.mark.django_db
class TestWIPCreate:
    def test_create_wip_success(self, client, auth_headers, lab_staff, sample):
        """Lab staff can create a WIP for a sample."""
        payload = {"sample_id": sample.pk}
        resp = client.post(
            "/api/wips/",
            data=payload,
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["sample_id"] == sample.pk
        assert data["status"] == WIPStatus.CREATED

    def test_create_wip_sample_not_found(self, client, auth_headers, lab_staff):
        """Returns 404 if sample does not exist."""
        resp = client.post(
            "/api/wips/",
            data={"sample_id": 99999},
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 404

    def test_create_wip_duplicate_sample_rejected(
        self, client, auth_headers, lab_staff, sample
    ):
        """Cannot create two WIPs for the same sample."""
        WIPFactory(sample=sample, created_by=lab_staff)
        resp = client.post(
            "/api/wips/",
            data={"sample_id": sample.pk},
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 409

    def test_create_wip_fab_user_forbidden(
        self, client, auth_headers, fab_user, sample
    ):
        """Fab user cannot create WIPs."""
        resp = client.post(
            "/api/wips/",
            data={"sample_id": sample.pk},
            content_type="application/json",
            **auth_headers(fab_user),
        )
        assert resp.status_code == 403


@pytest.mark.django_db
class TestWIPDetail:
    def test_get_wip_detail_includes_dispatches(
        self, client, auth_headers, lab_staff, wip_in_progress, dispatch
    ):
        """WIP detail includes list of dispatches."""
        resp = client.get(f"/api/wips/{wip_in_progress.pk}/", **auth_headers(lab_staff))
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == wip_in_progress.pk
        assert len(data["dispatches"]) == 1
        assert data["dispatches"][0]["id"] == dispatch.pk

    def test_get_wip_not_found(self, client, auth_headers, lab_staff):
        """Returns 404 for unknown WIP."""
        resp = client.get("/api/wips/99999/", **auth_headers(lab_staff))
        assert resp.status_code == 404

    def test_get_wip_fab_user_forbidden(self, client, auth_headers, fab_user, wip):
        """Fab user cannot get WIP detail."""
        resp = client.get(f"/api/wips/{wip.pk}/", **auth_headers(fab_user))
        assert resp.status_code == 403


@pytest.mark.django_db
class TestWIPCreateDispatch:
    def test_create_dispatch_success(
        self,
        client,
        auth_headers,
        lab_staff,
        wip,
        experiment_type,
        equipment,
        recipe,
    ):
        """Lab staff can create a dispatch for a WIP."""
        payload = {
            "experiment_type_id": experiment_type.pk,
            "equipment_id": equipment.pk,
            "recipe_id": recipe.pk,
        }
        resp = client.post(
            f"/api/wips/{wip.pk}/dispatches/",
            data=payload,
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == WIPStatus.IN_PROGRESS  # WIP transitions to in_progress

        # WIP should now be in_progress
        wip.refresh_from_db()
        assert wip.status == WIPStatus.IN_PROGRESS

    def test_create_dispatch_equipment_lacks_capability(
        self, client, auth_headers, lab_staff, wip, recipe
    ):
        """Returns 400 if equipment lacks capability for experiment type."""
        other_experiment_type = ExperimentTypeFactory()
        resp = client.post(
            f"/api/wips/{wip.pk}/dispatches/",
            data={
                "experiment_type_id": other_experiment_type.pk,
                "equipment_id": recipe.equipment_id,
                "recipe_id": recipe.pk,
            },
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 400

    def test_create_dispatch_recipe_wrong_equipment(
        self,
        client,
        auth_headers,
        lab_staff,
        wip,
        experiment_type,
        equipment,
        recipe,
    ):
        """Returns 400 if recipe does not belong to the given equipment."""
        other_equipment = EquipmentFactory()
        EquipmentCapability.objects.create(
            equipment=other_equipment, experiment_type=experiment_type
        )
        resp = client.post(
            f"/api/wips/{wip.pk}/dispatches/",
            data={
                "experiment_type_id": experiment_type.pk,
                "equipment_id": other_equipment.pk,
                "recipe_id": recipe.pk,  # recipe belongs to original equipment
            },
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 400

    def test_create_dispatch_fab_user_forbidden(
        self, client, auth_headers, fab_user, wip, experiment_type, equipment, recipe
    ):
        """Fab user cannot create dispatches."""
        resp = client.post(
            f"/api/wips/{wip.pk}/dispatches/",
            data={
                "experiment_type_id": experiment_type.pk,
                "equipment_id": equipment.pk,
                "recipe_id": recipe.pk,
            },
            content_type="application/json",
            **auth_headers(fab_user),
        )
        assert resp.status_code == 403


@pytest.mark.django_db
class TestWIPComplete:
    def test_complete_wip_success(
        self, client, auth_headers, lab_staff, wip_in_progress, result_recorded_dispatch
    ):
        """Lab staff can complete WIP when all dispatches are completed."""
        # Complete the dispatch first
        result_recorded_dispatch.status = DispatchStatus.COMPLETED
        result_recorded_dispatch.save()

        resp = client.post(
            f"/api/wips/{wip_in_progress.pk}/complete/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == WIPStatus.COMPLETED

        # Sample should be auto-completed
        wip_in_progress.sample.refresh_from_db()
        assert wip_in_progress.sample.status == SampleStatus.COMPLETED

    def test_complete_wip_with_pending_dispatches_fails(
        self, client, auth_headers, lab_staff, wip_in_progress, dispatch
    ):
        """Cannot complete WIP if any dispatch is still in progress."""
        resp = client.post(
            f"/api/wips/{wip_in_progress.pk}/complete/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 400

    def test_complete_wip_auto_completes_request(self, client, auth_headers, lab_staff):
        """Completing last WIP auto-completes the parent request."""
        from apps.commissions.factories import RequestFactory

        req = RequestFactory(status=RequestStatus.IN_PROGRESS)
        s = SampleFactory(request=req, status=SampleStatus.SPLIT)
        w = WIPFactory(sample=s, status=WIPStatus.IN_PROGRESS, created_by=lab_staff)
        DispatchFactory(wip=w, status=DispatchStatus.COMPLETED, created_by=lab_staff)

        resp = client.post(
            f"/api/wips/{w.pk}/complete/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200

        req.refresh_from_db()
        assert req.status == RequestStatus.COMPLETED


@pytest.mark.django_db
class TestWIPAbort:
    def test_abort_wip_success(self, client, auth_headers, lab_staff, wip_in_progress):
        """Lab staff can abort a WIP in progress."""
        resp = client.post(
            f"/api/wips/{wip_in_progress.pk}/abort/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == WIPStatus.ABORTED

        # Sample should be marked processing_exception
        wip_in_progress.sample.refresh_from_db()
        assert wip_in_progress.sample.status == SampleStatus.PROCESSING_EXCEPTION

    def test_abort_wip_completed_fails(
        self, client, auth_headers, lab_staff, wip_in_progress
    ):
        """Cannot abort an already completed WIP."""
        wip_in_progress.status = WIPStatus.COMPLETED
        wip_in_progress.save()
        resp = client.post(
            f"/api/wips/{wip_in_progress.pk}/abort/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 400

    def test_abort_wip_fab_user_forbidden(self, client, auth_headers, fab_user, wip):
        """Fab user cannot abort WIPs."""
        resp = client.post(
            f"/api/wips/{wip.pk}/abort/",
            **auth_headers(fab_user),
        )
        assert resp.status_code == 403


# =============================================================================
# Dispatch API Tests
# =============================================================================


@pytest.mark.django_db
class TestDispatchList:
    def test_list_dispatches_as_lab_staff(
        self, client, auth_headers, lab_staff, dispatch
    ):
        """Lab staff can list dispatches."""
        resp = client.get("/api/dispatches/", **auth_headers(lab_staff))
        assert resp.status_code == 200
        data = resp.json()
        assert any(d["id"] == dispatch.pk for d in data)

    def test_list_dispatches_filter_by_status(
        self, client, auth_headers, lab_staff, dispatch, dispatched_dispatch
    ):
        """Dispatches can be filtered by status."""
        resp = client.get(
            f"/api/dispatches/?status={DispatchStatus.DISPATCHED}",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(d["status"] == DispatchStatus.DISPATCHED for d in data)

    def test_list_dispatches_filter_by_wip_id(
        self, client, auth_headers, lab_staff, dispatch
    ):
        """Dispatches can be filtered by wip_id."""
        resp = client.get(
            f"/api/dispatches/?wip_id={dispatch.wip_id}",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(d["wip_id"] == dispatch.wip_id for d in data)

    def test_list_dispatches_filter_by_equipment_id(
        self, client, auth_headers, lab_staff, dispatch
    ):
        """Dispatches can be filtered by equipment_id."""
        resp = client.get(
            f"/api/dispatches/?equipment_id={dispatch.equipment_id}",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(d["equipment_id"] == dispatch.equipment_id for d in data)

    def test_list_dispatches_fab_user_forbidden(self, client, auth_headers, fab_user):
        """Fab user cannot list dispatches."""
        resp = client.get("/api/dispatches/", **auth_headers(fab_user))
        assert resp.status_code == 403


@pytest.mark.django_db
class TestDispatchDetail:
    def test_get_dispatch_detail(self, client, auth_headers, lab_staff, dispatch):
        """Lab staff can get dispatch detail."""
        resp = client.get(f"/api/dispatches/{dispatch.pk}/", **auth_headers(lab_staff))
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == dispatch.pk
        assert data["result"] is None

    def test_get_dispatch_with_result(
        self, client, auth_headers, lab_staff, result_recorded_dispatch
    ):
        """Dispatch detail includes experiment result when present."""
        resp = client.get(
            f"/api/dispatches/{result_recorded_dispatch.pk}/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"] is not None
        assert data["result"]["verdict"] == ExperimentResult.Verdict.PASS

    def test_get_dispatch_not_found(self, client, auth_headers, lab_staff):
        """Returns 404 for unknown dispatch."""
        resp = client.get("/api/dispatches/99999/", **auth_headers(lab_staff))
        assert resp.status_code == 404

    def test_get_dispatch_fab_user_forbidden(
        self, client, auth_headers, fab_user, dispatch
    ):
        """Fab user cannot get dispatch detail."""
        resp = client.get(f"/api/dispatches/{dispatch.pk}/", **auth_headers(fab_user))
        assert resp.status_code == 403


@pytest.mark.django_db
class TestDispatchStart:
    def test_start_dispatch_from_pending(
        self, client, auth_headers, lab_staff, dispatch
    ):
        """Starting a pending dispatch moves it to running."""
        resp = client.post(
            f"/api/dispatches/{dispatch.pk}/start/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == DispatchStatus.RUNNING

    def test_start_dispatch_from_dispatched(
        self, client, auth_headers, lab_staff, dispatched_dispatch
    ):
        """Starting a dispatched dispatch moves it to running."""
        resp = client.post(
            f"/api/dispatches/{dispatched_dispatch.pk}/start/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == DispatchStatus.RUNNING

    def test_start_already_running_dispatch_fails(
        self, client, auth_headers, lab_staff, running_dispatch
    ):
        """Cannot start an already running dispatch."""
        resp = client.post(
            f"/api/dispatches/{running_dispatch.pk}/start/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 400

    def test_start_dispatch_fab_user_forbidden(
        self, client, auth_headers, fab_user, dispatch
    ):
        """Fab user cannot start dispatches."""
        resp = client.post(
            f"/api/dispatches/{dispatch.pk}/start/",
            **auth_headers(fab_user),
        )
        assert resp.status_code == 403


@pytest.mark.django_db
class TestDispatchUnload:
    def test_unload_from_running(
        self, client, auth_headers, lab_staff, running_dispatch
    ):
        """Lab staff can unload a running dispatch."""
        resp = client.post(
            f"/api/dispatches/{running_dispatch.pk}/unload/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == DispatchStatus.UNLOADED

    def test_unload_from_dispatched(
        self, client, auth_headers, lab_staff, dispatched_dispatch
    ):
        """Lab staff can unload a dispatched (but not started) dispatch."""
        resp = client.post(
            f"/api/dispatches/{dispatched_dispatch.pk}/unload/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == DispatchStatus.UNLOADED

    def test_unload_from_pending_fails(self, client, auth_headers, lab_staff, dispatch):
        """Cannot unload a pending dispatch."""
        resp = client.post(
            f"/api/dispatches/{dispatch.pk}/unload/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestDispatchRecordResult:
    def test_record_result_success(
        self, client, auth_headers, lab_staff, unloaded_dispatch
    ):
        """Lab staff can record result for unloaded dispatch."""
        payload = {
            "summary": "All tests passed",
            "verdict": "pass",
            "data": {"temperature": 150.0},
        }
        resp = client.post(
            f"/api/dispatches/{unloaded_dispatch.pk}/record-result/",
            data=payload,
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == DispatchStatus.RESULT_RECORDED
        assert data["result"]["verdict"] == "pass"
        assert data["result"]["data_source"] == ExperimentResult.DataSource.MANUAL

    def test_record_result_invalid_verdict_fails(
        self, client, auth_headers, lab_staff, unloaded_dispatch
    ):
        """Returns 422 for invalid verdict value."""
        resp = client.post(
            f"/api/dispatches/{unloaded_dispatch.pk}/record-result/",
            data={"summary": "test", "verdict": "unknown"},
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 422

    def test_record_result_wrong_status_fails(
        self, client, auth_headers, lab_staff, running_dispatch
    ):
        """Cannot record result for non-unloaded dispatch."""
        resp = client.post(
            f"/api/dispatches/{running_dispatch.pk}/record-result/",
            data={"summary": "test", "verdict": "pass"},
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestDispatchComplete:
    def test_complete_dispatch_success(
        self, client, auth_headers, lab_staff, result_recorded_dispatch
    ):
        """Lab staff can complete a result_recorded dispatch."""
        resp = client.post(
            f"/api/dispatches/{result_recorded_dispatch.pk}/complete/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == DispatchStatus.COMPLETED

    def test_complete_dispatch_wrong_status_fails(
        self, client, auth_headers, lab_staff, running_dispatch
    ):
        """Cannot complete a non-result_recorded dispatch."""
        resp = client.post(
            f"/api/dispatches/{running_dispatch.pk}/complete/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestDispatchReportException:
    def test_report_exception_from_running(
        self, client, auth_headers, lab_staff, running_dispatch
    ):
        """Lab staff can report exception from running dispatch."""
        payload = {"note": "Machine malfunction"}
        resp = client.post(
            f"/api/dispatches/{running_dispatch.pk}/report-exception/",
            data=payload,
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == DispatchStatus.EXECUTION_EXCEPTION

    def test_report_exception_from_dispatched(
        self, client, auth_headers, lab_staff, dispatched_dispatch
    ):
        """Lab staff can report exception from dispatched dispatch."""
        resp = client.post(
            f"/api/dispatches/{dispatched_dispatch.pk}/report-exception/",
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == DispatchStatus.EXECUTION_EXCEPTION

    def test_report_exception_from_pending_fails(
        self, client, auth_headers, lab_staff, dispatch
    ):
        """Cannot report exception from pending dispatch."""
        resp = client.post(
            f"/api/dispatches/{dispatch.pk}/report-exception/",
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestDispatchRedispatch:
    def test_redispatch_success(self, client, auth_headers, lab_staff, dispatch):
        """Lab staff can redispatch an exception dispatch, creating a new dispatch."""
        dispatch.status = DispatchStatus.EXECUTION_EXCEPTION
        dispatch.save()

        resp = client.post(
            f"/api/dispatches/{dispatch.pk}/redispatch/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == DispatchStatus.PENDING_REDISPATCH

        # A new dispatch should be created at PENDING for the same WIP
        new_dispatches = Dispatch.objects.filter(
            wip=dispatch.wip, status=DispatchStatus.PENDING
        )
        assert new_dispatches.count() == 1

    def test_redispatch_wrong_status_fails(
        self, client, auth_headers, lab_staff, running_dispatch
    ):
        """Cannot redispatch from non-exception status."""
        resp = client.post(
            f"/api/dispatches/{running_dispatch.pk}/redispatch/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestDispatchAbort:
    def test_abort_dispatch_from_exception(
        self, client, auth_headers, lab_staff, dispatch
    ):
        """Lab staff can abort a dispatch in execution_exception state."""
        dispatch.status = DispatchStatus.EXECUTION_EXCEPTION
        dispatch.save()

        resp = client.post(
            f"/api/dispatches/{dispatch.pk}/abort/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == DispatchStatus.ABORTED

    def test_abort_dispatch_from_pending(
        self, client, auth_headers, lab_staff, dispatch
    ):
        """Lab staff can abort a pending dispatch."""
        resp = client.post(
            f"/api/dispatches/{dispatch.pk}/abort/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == DispatchStatus.ABORTED

    def test_abort_completed_dispatch_fails(
        self, client, auth_headers, lab_staff, dispatch
    ):
        """Cannot abort a completed dispatch."""
        dispatch.status = DispatchStatus.COMPLETED
        dispatch.save()
        resp = client.post(
            f"/api/dispatches/{dispatch.pk}/abort/",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 400

    def test_abort_dispatch_lab_manager_allowed(
        self, client, auth_headers, lab_manager, dispatch
    ):
        """Lab manager can also abort a dispatch."""
        resp = client.post(
            f"/api/dispatches/{dispatch.pk}/abort/",
            **auth_headers(lab_manager),
        )
        assert resp.status_code == 200

    def test_abort_dispatch_fab_user_forbidden(
        self, client, auth_headers, fab_user, dispatch
    ):
        """Fab user cannot abort dispatches."""
        resp = client.post(
            f"/api/dispatches/{dispatch.pk}/abort/",
            **auth_headers(fab_user),
        )
        assert resp.status_code == 403


# =============================================================================
# Automation API Tests
# =============================================================================


@pytest.mark.django_db
class TestAutomationEquipmentResult:
    def test_automation_result_completes_dispatch(
        self, client, auth_headers, lab_staff, dispatched_dispatch
    ):
        """Automation endpoint completes dispatch with automated data_source."""
        payload = {
            "dispatch_id": dispatched_dispatch.pk,
            "summary": "Automated measurement complete",
            "verdict": "pass",
            "data": {"measurement": 99.5},
        }
        resp = client.post(
            "/api/automation/equipment-result/",
            data=payload,
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == DispatchStatus.COMPLETED

        result = ExperimentResult.objects.get(dispatch_id=dispatched_dispatch.pk)
        assert result.data_source == ExperimentResult.DataSource.AUTOMATED
        assert result.verdict == ExperimentResult.Verdict.PASS

    def test_automation_result_from_running_dispatch(
        self, client, auth_headers, lab_staff, running_dispatch
    ):
        """Automation endpoint works for running dispatch too."""
        payload = {
            "dispatch_id": running_dispatch.pk,
            "summary": "Done",
            "verdict": "fail",
            "data": {},
        }
        resp = client.post(
            "/api/automation/equipment-result/",
            data=payload,
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200

    def test_automation_result_triggers_linkage(self, client, auth_headers, lab_staff):
        """Automation completing last dispatch allows WIP completion linkage check."""
        from apps.commissions.factories import RequestFactory

        req = RequestFactory(status=RequestStatus.IN_PROGRESS)
        s = SampleFactory(request=req, status=SampleStatus.SPLIT)
        w = WIPFactory(sample=s, status=WIPStatus.IN_PROGRESS, created_by=lab_staff)
        d = DispatchFactory(
            wip=w, status=DispatchStatus.DISPATCHED, created_by=lab_staff
        )

        payload = {
            "dispatch_id": d.pk,
            "summary": "Automated",
            "verdict": "pass",
            "data": {},
        }
        resp = client.post(
            "/api/automation/equipment-result/",
            data=payload,
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 200
        # Dispatch completed; WIP is still in_progress (manual complete required)
        w.refresh_from_db()
        assert w.status == WIPStatus.IN_PROGRESS

    def test_automation_result_wrong_status_fails(
        self, client, auth_headers, lab_staff, unloaded_dispatch
    ):
        """Automation endpoint rejects dispatches not in dispatched/running state."""
        payload = {
            "dispatch_id": unloaded_dispatch.pk,
            "summary": "Test",
            "verdict": "pass",
            "data": {},
        }
        resp = client.post(
            "/api/automation/equipment-result/",
            data=payload,
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 400

    def test_automation_result_dispatch_not_found(
        self, client, auth_headers, lab_staff
    ):
        """Returns 404 if dispatch not found."""
        payload = {
            "dispatch_id": 99999,
            "summary": "Test",
            "verdict": "pass",
            "data": {},
        }
        resp = client.post(
            "/api/automation/equipment-result/",
            data=payload,
            content_type="application/json",
            **auth_headers(lab_staff),
        )
        assert resp.status_code == 404

    def test_automation_result_fab_user_forbidden(
        self, client, auth_headers, fab_user, dispatched_dispatch
    ):
        """Fab user cannot submit automation results."""
        payload = {
            "dispatch_id": dispatched_dispatch.pk,
            "summary": "Test",
            "verdict": "pass",
            "data": {},
        }
        resp = client.post(
            "/api/automation/equipment-result/",
            data=payload,
            content_type="application/json",
            **auth_headers(fab_user),
        )
        assert resp.status_code == 403
