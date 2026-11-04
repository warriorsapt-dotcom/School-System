from .models import SchoolConfiguration


def school_configuration(request):
    return {'school_config': SchoolConfiguration.current()}
