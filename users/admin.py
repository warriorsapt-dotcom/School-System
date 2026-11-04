from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Teacher, Student, Admin, SchoolImage


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )


admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(Admin)
admin.site.register(SchoolImage)


from .models import SchoolConfiguration


@admin.register(SchoolConfiguration)
class SchoolConfigurationAdmin(admin.ModelAdmin):
    fields = ['school_name', 'account_suffix']

    def has_add_permission(self, request):
        return super().has_add_permission(request) and not SchoolConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
