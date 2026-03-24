from django.contrib.auth.models import User
from django.db import models


class WIPStatus(models.TextChoices):
    CREATED = "created", "已建立"
    PENDING_DISPATCH = "pending_dispatch", "待派貨"
    DISPATCHED = "dispatched", "已派貨"
    RUNNING = "running", "執行中"
    EXECUTION_EXCEPTION = "execution_exception", "執行異常"
    UNLOADED = "unloaded", "已下貨"
    RESULT_RECORDED = "result_recorded", "結果已登錄"
    COMPLETED = "completed", "已完成"
    ABORTED = "aborted", "已中止"
    PENDING_REDISPATCH = "pending_redispatch", "待重派"


class WIP(models.Model):
    """Work In Progress: a virtual processing unit grouping samples for a single experiment run."""

    experiment_type = models.ForeignKey(
        "experiments.ExperimentType",
        on_delete=models.PROTECT,
        related_name="wips",
    )
    samples = models.ManyToManyField(
        "commissions.Sample",
        through="WIPSample",
        related_name="wips",
    )
    equipment = models.ForeignKey(
        "equipment.Equipment",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="wips",
    )
    recipe = models.ForeignKey(
        "equipment.Recipe",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="wips",
    )
    status = models.CharField(
        max_length=30, choices=WIPStatus.choices, default=WIPStatus.CREATED
    )
    note = models.TextField(blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="created_wips"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wip"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["equipment", "status"]),
            models.Index(fields=["dispatched_at"]),
        ]

    def __str__(self):
        return f"WIP #{self.pk} ({self.status})"


class WIPSample(models.Model):
    """Through model linking a WIP to its samples."""

    wip = models.ForeignKey(WIP, on_delete=models.CASCADE, related_name="wip_samples")
    sample = models.ForeignKey(
        "commissions.Sample", on_delete=models.CASCADE, related_name="wip_samples"
    )

    class Meta:
        db_table = "wip_sample"
        unique_together = ("wip", "sample")

    def __str__(self):
        return f"WIP #{self.wip_id} ↔ Sample #{self.sample_id}"


class ExperimentResult(models.Model):
    """Experiment result record for a completed WIP."""

    class DataSource(models.TextChoices):
        MANUAL = "manual", "手動登錄"
        AUTOMATED = "automated", "自動化"

    class Verdict(models.TextChoices):
        PASS = "pass", "合格"
        FAIL = "fail", "不合格"

    wip = models.OneToOneField(WIP, on_delete=models.CASCADE, related_name="result")
    summary = models.TextField()
    verdict = models.CharField(max_length=10, choices=Verdict.choices)
    data = models.JSONField(default=dict, blank=True)
    data_source = models.CharField(
        max_length=20,
        choices=DataSource.choices,
        default=DataSource.MANUAL,
    )
    note = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="recorded_results",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "experiment_result"

    def __str__(self):
        return f"Result for WIP #{self.wip_id}: {self.verdict}"
