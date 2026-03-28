from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from apps.wip.models import WIP, Dispatch, ExperimentResult


class DispatchInline(TabularInline):
    model = Dispatch
    extra = 0
    fields = (
        "experiment_type",
        "equipment",
        "recipe",
        "status",
        "dispatched_at",
        "completed_at",
        "created_at",
    )
    readonly_fields = ("dispatched_at", "completed_at", "created_at")
    show_change_link = True


class ExperimentResultInline(TabularInline):
    model = ExperimentResult
    extra = 0
    fields = ("summary", "verdict", "data_source", "recorded_by", "created_at")
    readonly_fields = ("summary", "verdict", "data_source", "recorded_by", "created_at")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WIP)
class WIPAdmin(ModelAdmin):
    list_display = (
        "id",
        "sample",
        "status",
        "created_by",
        "completed_at",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("sample__wafer_id", "created_by__username")
    readonly_fields = ("completed_at", "created_at", "updated_at")
    list_select_related = ("sample", "created_by")
    list_per_page = 25
    inlines = (DispatchInline,)


@admin.register(Dispatch)
class DispatchAdmin(ModelAdmin):
    list_display = (
        "id",
        "wip",
        "experiment_type",
        "equipment",
        "status",
        "dispatched_at",
        "completed_at",
        "created_at",
    )
    list_filter = ("status", "equipment", "experiment_type")
    search_fields = (
        "wip__sample__wafer_id",
        "equipment__name",
        "experiment_type__name",
        "created_by__username",
    )
    readonly_fields = ("dispatched_at", "completed_at", "created_at", "updated_at")
    list_select_related = ("wip", "experiment_type", "equipment", "recipe")
    list_per_page = 25
    inlines = (ExperimentResultInline,)


@admin.register(ExperimentResult)
class ExperimentResultAdmin(ModelAdmin):
    list_display = (
        "id",
        "dispatch",
        "verdict",
        "data_source",
        "recorded_by",
        "created_at",
    )
    list_filter = ("verdict", "data_source")
    search_fields = (
        "dispatch__wip__sample__wafer_id",
        "summary",
        "recorded_by__username",
    )
    readonly_fields = (
        "dispatch",
        "summary",
        "verdict",
        "data",
        "data_source",
        "recorded_by",
        "created_at",
    )
    list_select_related = ("dispatch", "recorded_by")
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
