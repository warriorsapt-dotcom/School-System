from django.contrib import admin
from .models import Class, Subject, ClassSubject, Term

admin.site.register(Class)
admin.site.register(Subject)
admin.site.register(ClassSubject)
admin.site.register(Term)
