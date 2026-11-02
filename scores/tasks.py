from celery import shared_task
from django.core.management import call_command


@shared_task
def generate_term_results_async(term_id=None, class_name=None):
    args = []
    if term_id:
        args += ['--term', str(term_id)]
    if class_name:
        args += ['--class', class_name]
    call_command('generate_term_results', *args)
    return f'Term results generated (term={term_id}, class={class_name})'
