from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from django.db.models import Q
from django.http import FileResponse, Http404
from django.utils import timezone
from PIL import Image
from rest_framework import mixins, permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Assignment, Class


def teaching_classes(user):
    return Class.objects.filter(Q(class_teacher__user=user) | Q(class_subjects__teacher__user=user)).distinct()


class AssignmentSerializer(serializers.ModelSerializer):
    deadline = serializers.DateTimeField(required=True, allow_null=False)
    file = serializers.FileField(write_only=True, required=False, max_length=255)
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'class_obj', 'class_name', 'instructions', 'teacher_name', 'published', 'deadline', 'filename', 'file']
        read_only_fields = ['filename', 'published']

    def validate_class_obj(self, value):
        if not teaching_classes(self.context['request'].user).filter(pk=value.pk).exists():
            raise serializers.ValidationError('Choose a class you teach.')
        return value

    def validate_deadline(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError('Choose a deadline in the future.')
        return value

    def validate_file(self, file):
        if file.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('Choose a file of 10 MB or less.')
        ext = Path(file.name).suffix.lower()
        data = file.read()
        valid = False
        try:
            if ext == '.pdf':
                valid = data.startswith(b'%PDF-')
            elif ext == '.doc':
                valid = data.startswith(bytes.fromhex('D0CF11E0A1B11AE1'))
            elif ext == '.docx':
                with ZipFile(BytesIO(data)) as archive:
                    valid = {'[Content_Types].xml', 'word/document.xml'} <= set(archive.namelist())
            elif ext in ('.png', '.jpg', '.jpeg', '.webp'):
                with Image.open(BytesIO(data)) as picture:
                    valid = picture.format == {'.png':'PNG', '.jpg':'JPEG', '.jpeg':'JPEG', '.webp':'WEBP'}[ext]
                    picture.verify()
        except (BadZipFile, OSError, ValueError, SyntaxError, Image.DecompressionBombError):
            valid = False
        if not valid:
            raise serializers.ValidationError('Choose a Word document, PDF, PNG, JPEG or WebP image matching its extension.')
        file.seek(0)
        return file

    def validate(self, attrs):
        if not attrs.get('instructions') and not attrs.get('file'):
            raise serializers.ValidationError('Type instructions or attach a file.')
        return attrs

    def create(self, validated_data):
        upload = validated_data.pop('file', None)
        if upload:
            validated_data.update(filename=upload.name, attachment=upload.read())
        return Assignment.objects.create(**validated_data)


class AssignmentPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.method in permissions.SAFE_METHODS or request.user.role == 'teacher')


class AssignmentViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [AssignmentPermission]

    def get_queryset(self):
        user = self.request.user
        qs = Assignment.objects.select_related('class_obj', 'teacher__user')
        if self.action != 'download':
            qs = qs.defer('attachment')
        if user.role == 'student':
            return qs.filter(class_obj__students__user=user).filter(
                Q(deadline__isnull=True) | Q(deadline__gt=timezone.now())
            )
        if user.role == 'teacher':
            return qs.filter(class_obj__in=teaching_classes(user))
        return qs if user.role in ('admin', 'principal') else qs.none()

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user.teacher_profile)

    @action(detail=False)
    def choices(self, request):
        return Response(list(teaching_classes(request.user).values('id', 'name')) if request.user.role == 'teacher' else [])

    @action(detail=True)
    def download(self, request, pk=None):
        assignment = self.get_object()
        if not assignment.filename:
            raise Http404
        return FileResponse(BytesIO(assignment.attachment), as_attachment=True, filename=assignment.filename,
                            content_type='application/octet-stream')
