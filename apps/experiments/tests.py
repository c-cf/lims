import pytest
from django.db import IntegrityError


@pytest.mark.django_db
class TestExperimentType:
    def test_create_experiment_type(self):
        """ExperimentType can be created successfully."""
        from apps.experiments.models import ExperimentType, LabCategory

        exp = ExperimentType.objects.create(
            name="高溫烘烤測試",
            description="在高溫環境下測試晶圓可靠度",
            lab_category=LabCategory.RA,
        )

        assert exp.name == "高溫烘烤測試"
        assert exp.lab_category == LabCategory.RA
        assert exp.is_active is True
        assert exp.created_at is not None
        assert exp.updated_at is not None

    def test_name_unique_constraint(self):
        """ExperimentType name must be unique."""
        from apps.experiments.models import ExperimentType, LabCategory

        ExperimentType.objects.create(name="測試項目 A", lab_category=LabCategory.MA)

        with pytest.raises(IntegrityError):
            ExperimentType.objects.create(
                name="測試項目 A", lab_category=LabCategory.FA
            )

    def test_soft_delete(self):
        """Setting is_active=False soft-deletes the record while keeping it in the DB."""
        from apps.experiments.models import ExperimentType, LabCategory

        exp = ExperimentType.objects.create(
            name="已停用項目", lab_category=LabCategory.TM
        )
        exp.is_active = False
        exp.save()

        assert ExperimentType.objects.filter(name="已停用項目").exists()
        assert not ExperimentType.objects.get(name="已停用項目").is_active

    def test_description_optional(self):
        """description field defaults to an empty string."""
        from apps.experiments.models import ExperimentType, LabCategory

        exp = ExperimentType.objects.create(
            name="無描述項目", lab_category=LabCategory.RA
        )
        assert exp.description == ""

    def test_db_table_name(self):
        """Database table name is experiment_type."""
        from apps.experiments.models import ExperimentType

        assert ExperimentType._meta.db_table == "experiment_type"


@pytest.mark.django_db
class TestLabCategory:
    def test_lab_category_values(self):
        """LabCategory contains the four expected values."""
        from apps.experiments.models import LabCategory

        assert LabCategory.RA == "RA"
        assert LabCategory.MA == "MA"
        assert LabCategory.FA == "FA"
        assert LabCategory.TM == "TM"
