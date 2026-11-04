from rest_framework import serializers
from .models import CustomUser, Teacher, Student, Admin, SchoolImage, SchoolConfiguration
from .validators import validate_account_id, validate_account_suffix
from rest_framework.validators import UniqueValidator
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError


class SchoolAccountField(serializers.CharField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if '@' not in value:
            value = f'{value}@{SchoolConfiguration.current().account_suffix}'
        local, domain = value.rsplit('@', 1)
        value = local + '@' + domain.lower()
        try:
            validate_account_id(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)
        if len(value) > 150:
            raise serializers.ValidationError('Login ID must be at most 150 characters.')
        return value


class SchoolConfigurationSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(max_length=150)
    account_suffix = serializers.CharField(max_length=100, validators=[validate_account_suffix])

    class Meta:
        model = SchoolConfiguration
        fields = ['school_name', 'account_suffix']

    def to_internal_value(self, data):
        data = data.copy()
        if isinstance(data.get('account_suffix'), str):
            data['account_suffix'] = data['account_suffix'].strip().lower()
        return super().to_internal_value(data)



def _pop_user_fields(validated_data):
    return {
        'email': validated_data.pop('email', None),
        'first_name': validated_data.pop('first_name', ''),
        'last_name': validated_data.pop('last_name', ''),
        'password': validated_data.pop('password', 'changeme123'),
    }


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'phone_number',
                  'role', 'password', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at', 'email', 'username', 'role', 'is_active']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class TeacherSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    # Write-only fields for creation
    email = SchoolAccountField(write_only=True, validators=[UniqueValidator(queryset=CustomUser.objects.all())])
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Teacher
        fields = ['id', 'user', 'email', 'first_name', 'last_name', 'password',
                  'employee_id', 'qualification', 'subject_specialization',
                  'bio', 'hire_date', 'is_class_teacher', 'is_active']
        read_only_fields = ['id']

    @transaction.atomic
    def create(self, validated_data):
        uf = _pop_user_fields(validated_data)
        user = CustomUser.objects.create_user(
            email=uf['email'], username=uf['email'],
            first_name=uf['first_name'], last_name=uf['last_name'],
            password=uf['password'], role='teacher',
        )
        return Teacher.objects.create(user=user, **validated_data)


class StudentSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    class_assigned_name = serializers.CharField(source='class_assigned.name', read_only=True)
    # Write-only fields for creation
    email = SchoolAccountField(write_only=True, validators=[UniqueValidator(queryset=CustomUser.objects.all())])
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Student
        fields = ['id', 'user', 'email', 'first_name', 'last_name', 'password',
                  'admission_number', 'class_assigned', 'class_assigned_name',
                  'date_of_birth', 'parent_name', 'parent_contact', 'parent_email',
                  'address', 'is_active']
        read_only_fields = ['id']

    @transaction.atomic
    def create(self, validated_data):
        uf = _pop_user_fields(validated_data)
        user = CustomUser.objects.create_user(
            email=uf['email'], username=uf['email'],
            first_name=uf['first_name'], last_name=uf['last_name'],
            password=uf['password'], role='student',
        )
        return Student.objects.create(user=user, **validated_data)


class AdminSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)

    class Meta:
        model = Admin
        fields = ['id', 'user', 'employee_id', 'department', 'designation']
        read_only_fields = ['id']


class SchoolImageSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)

    class Meta:
        model = SchoolImage
        fields = ['id', 'title', 'description', 'image', 'category', 'uploaded_by',
                  'uploaded_by_name', 'is_published', 'created_at']
        read_only_fields = ['id', 'created_at', 'uploaded_by']


class LoginSerializer(serializers.Serializer):
    email = SchoolAccountField()
    password = serializers.CharField(write_only=True)


class RegistrationSerializer(serializers.ModelSerializer):
    email = SchoolAccountField(validators=[UniqueValidator(queryset=CustomUser.objects.all())])

    def validate_role(self, value):
        request = self.context.get('request')
        if value != 'student' and not (request and request.user.is_authenticated and request.user.role == 'admin'):
            raise serializers.ValidationError('Only an administrator can assign this role.')
        return value

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name', 'password', 'password_confirm', 'role']

    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({'password': 'Passwords must match'})
        return data

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password': 'Passwords must match'})
        return data
