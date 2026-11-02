from django.contrib import admin
from .models import Score, ScoreComment, SubjectPerformance, TermResult, YearlyResult, ProgressLog

admin.site.register(Score)
admin.site.register(ScoreComment)
admin.site.register(SubjectPerformance)
admin.site.register(TermResult)
admin.site.register(YearlyResult)
admin.site.register(ProgressLog)
