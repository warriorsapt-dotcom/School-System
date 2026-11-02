from datetime import date
from django.core.management.base import BaseCommand
from classes.models import Class, Term
from scores.utils import ResultCalculation


class Command(BaseCommand):
    help = 'Generate term results for a specific class'

    def add_arguments(self, parser):
        parser.add_argument('--term', type=str, help='Term name (first, second, third)')
        parser.add_argument('--class', type=str, dest='class_name', help='Class name')
        parser.add_argument('--year', type=str, default=str(date.today().year), help='Academic year e.g. 2024/2025')

    def handle(self, *args, **options):
        term_name = options.get('term')
        class_name = options.get('class_name')
        year = options.get('year')

        try:
            term = Term.objects.get(name=term_name, academic_year__startswith=year.split('/')[0])
            class_obj = Class.objects.get(name=class_name)
            results = ResultCalculation.generate_term_results(class_obj, term)
            self.stdout.write(self.style.SUCCESS(
                f'Successfully generated results for {len(results)} students in {class_name}'
            ))
        except Term.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Term "{term_name}" for year "{year}" not found'))
        except Class.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Class "{class_name}" not found'))
