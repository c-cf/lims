import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError


@pytest.fixture
def lab_user():
    return User.objects.create_user(username="lab_staff", password="pass")


@pytest.fixture
def experiment_type():
    from apps.experiments.models import ExperimentType, LabCategory

    return ExperimentType.objects.create(name="高溫烘烤", lab_category=LabCategory.RA)


@pytest.fixture
def equipment(experiment_type):
    from apps.equipment.models import Equipment, EquipmentCapability

    equip = Equipment.objects.create(
        name="烤箱 A-01", model_name="OV-3000", capacity=25
    )
    EquipmentCapability.objects.create(equipment=equip, experiment_type=experiment_type)
    return equip


@pytest.fixture
def recipe(equipment, experiment_type):
    from apps.equipment.models import Recipe

    return Recipe.objects.create(
        name="測試 Recipe",
        equipment=equipment,
        experiment_type=experiment_type,
    )


@pytest.fixture
def request_obj(lab_user):
    from apps.commissions.models import Request

    return Request.objects.create(title="測試委託", requester=lab_user)


@pytest.fixture
def sample(request_obj):
    from apps.commissions.models import Sample, WaferSize

    return Sample.objects.create(
        request=request_obj, wafer_id="WF-001", wafer_size=WaferSize.SIZE_300MM
    )


@pytest.mark.django_db
class TestWIP:
    def test_create_wip(self, lab_user, experiment_type):
        """WIP can be created; equipment and recipe are null before dispatch."""
        from apps.wip.models import WIP, WIPStatus

        wip = WIP.objects.create(
            experiment_type=experiment_type,
            created_by=lab_user,
        )

        assert wip.experiment_type == experiment_type
        assert wip.status == WIPStatus.CREATED
        assert wip.equipment is None
        assert wip.recipe is None
        assert wip.created_by == lab_user

    def test_wip_sample_m2m(self, lab_user, experiment_type, sample):
        """WIP can be linked to multiple Samples via WIPSample."""
        from apps.wip.models import WIP, WIPSample

        wip = WIP.objects.create(
            experiment_type=experiment_type,
            created_by=lab_user,
        )
        WIPSample.objects.create(wip=wip, sample=sample)

        assert wip.samples.count() == 1
        assert sample in wip.samples.all()

    def test_wip_sample_unique_together(self, lab_user, experiment_type, sample):
        """Duplicate WIPSample entries for the same WIP and Sample are rejected."""
        from apps.wip.models import WIP, WIPSample

        wip = WIP.objects.create(
            experiment_type=experiment_type,
            created_by=lab_user,
        )
        WIPSample.objects.create(wip=wip, sample=sample)

        with pytest.raises(IntegrityError):
            WIPSample.objects.create(wip=wip, sample=sample)

    def test_wip_equipment_nullable_before_dispatch(self, lab_user, experiment_type):
        """equipment and recipe are nullable before dispatch."""
        from apps.wip.models import WIP

        wip = WIP.objects.create(
            experiment_type=experiment_type,
            created_by=lab_user,
        )
        assert wip.equipment is None
        assert wip.recipe is None

    def test_wip_db_table_name(self):
        """Database table name is wip."""
        from apps.wip.models import WIP

        assert WIP._meta.db_table == "wip"

    def test_wip_sample_db_table_name(self):
        """Database table name is wip_sample."""
        from apps.wip.models import WIPSample

        assert WIPSample._meta.db_table == "wip_sample"


@pytest.mark.django_db
class TestExperimentResult:
    def test_create_experiment_result(self, lab_user, experiment_type):
        """ExperimentResult can be created with a OneToOne relation to WIP."""
        from apps.wip.models import WIP, ExperimentResult

        wip = WIP.objects.create(
            experiment_type=experiment_type,
            created_by=lab_user,
        )
        result = ExperimentResult.objects.create(
            wip=wip,
            summary="測試完成，所有樣品通過",
            verdict=ExperimentResult.Verdict.PASS,
        )

        assert result.wip == wip
        assert result.verdict == ExperimentResult.Verdict.PASS
        assert result.data_source == ExperimentResult.DataSource.MANUAL

    def test_experiment_result_one_to_one(self, lab_user, experiment_type):
        """A WIP can have at most one ExperimentResult."""
        from apps.wip.models import WIP, ExperimentResult

        wip = WIP.objects.create(
            experiment_type=experiment_type,
            created_by=lab_user,
        )
        ExperimentResult.objects.create(
            wip=wip,
            summary="第一次結果",
            verdict=ExperimentResult.Verdict.PASS,
        )

        with pytest.raises(IntegrityError):
            ExperimentResult.objects.create(
                wip=wip,
                summary="重複結果",
                verdict=ExperimentResult.Verdict.FAIL,
            )

    def test_experiment_result_json_data(self, lab_user, experiment_type):
        """data JSONField can be written and read back correctly."""
        from apps.wip.models import WIP, ExperimentResult

        wip = WIP.objects.create(
            experiment_type=experiment_type,
            created_by=lab_user,
        )
        data = {"temperature_actual": 150.2, "defect_count": 0}
        result = ExperimentResult.objects.create(
            wip=wip,
            summary="帶數據的結果",
            verdict=ExperimentResult.Verdict.PASS,
            data=data,
        )

        fresh = ExperimentResult.objects.get(pk=result.pk)
        assert fresh.data["temperature_actual"] == 150.2
        assert fresh.data["defect_count"] == 0

    def test_experiment_result_db_table_name(self):
        """Database table name is experiment_result."""
        from apps.wip.models import ExperimentResult

        assert ExperimentResult._meta.db_table == "experiment_result"
