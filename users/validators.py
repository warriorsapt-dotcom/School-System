import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


def validate_account_id(value):
    """Accept normal email addresses and internal school IDs such as mary@ksc."""
    try:
        validate_email(value)
        return
    except ValidationError:
        if re.fullmatch(r"[A-Za-z0-9_+.-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", value):
            local = value.split('@')[0]
            if not local.startswith('.') and not local.endswith('.') and '..' not in local:
                return
    raise ValidationError('Enter an email address or school login ID such as mary@ksc.')


def validate_account_suffix(value):
    label = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    if not re.fullmatch(label + r"(?:\." + label + r")*", value):
        raise ValidationError('Use a suffix such as ksc, ktp or school.example.org, without @ or spaces.')
