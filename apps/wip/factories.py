"""Factory classes for the wip app, used in tests."""

import factory
from factory.django import DjangoModelFactory

from apps.accounts.factories import UserFactory
from apps.commissions.factories import SampleFactory
from apps.equipment.factories import EquipmentFactory, RecipeFactory
from apps.experiments.factories import ExperimentTypeFactory
from apps.wip.models import WIP, Dispatch, DispatchStatus, ExperimentResult, WIPStatus


class WIPFactory(DjangoModelFactory):
    """Factory for WIP instances."""

    class Meta:
        model = WIP

    sample = factory.SubFactory(SampleFactory)
    status = WIPStatus.CREATED
    note = ""
    created_by = factory.SubFactory(UserFactory)


class DispatchFactory(DjangoModelFactory):
    """Factory for Dispatch instances."""

    class Meta:
        model = Dispatch

    wip = factory.SubFactory(WIPFactory)
    experiment_type = factory.SubFactory(ExperimentTypeFactory)
    equipment = factory.SubFactory(EquipmentFactory)
    recipe = factory.SubFactory(RecipeFactory)
    status = DispatchStatus.PENDING
    note = ""
    created_by = factory.SubFactory(UserFactory)


class ExperimentResultFactory(DjangoModelFactory):
    """Factory for ExperimentResult instances."""

    class Meta:
        model = ExperimentResult

    dispatch = factory.SubFactory(DispatchFactory)
    summary = factory.Sequence(lambda n: f"Test result {n}")
    verdict = ExperimentResult.Verdict.PASS
    data = factory.LazyFunction(dict)
    data_source = ExperimentResult.DataSource.MANUAL
