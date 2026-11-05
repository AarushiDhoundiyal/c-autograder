from django.contrib import admin

from .models import Flag, GradingRun, MetricResult, Problem, RuleSet, Submission

admin.site.register(Problem)
admin.site.register(RuleSet)
admin.site.register(Submission)
admin.site.register(MetricResult)
admin.site.register(Flag)


@admin.register(GradingRun)
class GradingRunAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "status", "grade", "partial", "created_at")
    list_filter = ("status", "partial")
