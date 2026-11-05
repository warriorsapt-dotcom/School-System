from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Teacher, Student, Admin, SchoolImage


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'student_class', 'is_active']
    list_select_related = ('student_profile__class_assigned',)
    list_filter = ['role', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']

    @admin.display(description='Class', ordering='student_profile__class_assigned__name', empty_value='—')
    def student_class(self, user):
        if user.role != 'student':
            return None
        profile = getattr(user, 'student_profile', None)
        return profile.class_assigned.name if profile and profile.class_assigned_id else 'Unassigned'

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )


class SchoolProfileForm(forms.ModelForm):
    def clean_user(self):
        account = self.cleaned_data['user']
        # Admin saves run in a transaction. Serialize competing profile additions.
        account = CustomUser.objects.select_for_update().get(pk=account.pk)
        if not self.fields['user'].queryset.filter(pk=account.pk).exists():
            raise forms.ValidationError('Choose an available school account.')
        return account


class SchoolProfileAdmin(admin.ModelAdmin):
    form = SchoolProfileForm

    def get_readonly_fields(self, request, obj=None):
        return ('user',) if obj else ()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            accounts = CustomUser.objects.filter(
                role__in=('student', 'teacher'), is_staff=False, is_superuser=False,
                student_profile__isnull=True, teacher_profile__isnull=True, admin_profile__isnull=True,
            )
            if not request.user.has_perm('users.change_customuser'):
                accounts = accounts.filter(role=self.model._meta.model_name)
            kwargs['queryset'] = accounts
            kwargs['help_text'] = f'Saving grants this account {self.model._meta.verbose_name.lower()} access to the school dashboard.'
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and obj.user.role != self.model._meta.model_name:
            obj.user.role = self.model._meta.model_name
            obj.user.save(update_fields=['role'])


admin.site.register(Teacher, SchoolProfileAdmin)
admin.site.register(Student, SchoolProfileAdmin)
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
