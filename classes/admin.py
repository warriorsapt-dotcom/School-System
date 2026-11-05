from django.contrib import admin
from .models import Class, Subject, ClassSubject, Term

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'class_teacher', 'capacity', 'is_active')
    list_filter = ('year', 'is_active')
    search_fields = ('name', 'class_teacher__user__first_name', 'class_teacher__user__last_name')
    list_select_related = ('class_teacher__user',)


admin.site.register(Subject)
admin.site.register(ClassSubject)
admin.site.register(Term)
