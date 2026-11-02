"""
Utility Functions and Management Commands for School Platform
Place utility functions in a utils.py file and management commands in apps/management/commands/
"""

# ============== Utility Functions ==============

from decimal import Decimal
from django.db.models import Avg, Count, Q
from datetime import date, timedelta
from django.utils import timezone
from scores.models import Score, TermResult, YearlyResult, ProgressLog, SubjectPerformance
from attendance.models import Attendance, AttendanceSummary
from classes.models import Term, Class
from users.models import Student


class AcademicCalculations:
    """Utility class for academic calculations"""
    
    @staticmethod
    def calculate_subject_performance(student, subject, term):
        """
        Calculate performance for a subject in a term
        """
        scores = Score.objects.filter(
            student=student,
            subject=subject,
            term=term,
            is_approved=True
        )
        
        if not scores.exists():
            return None
        
        total_marks = scores.aggregate(Avg('marks_obtained'))['marks_obtained__avg']
        total_max_marks = scores.aggregate(Avg('max_marks'))['max_marks__avg']
        
        if total_max_marks and total_max_marks > 0:
            percentage = (total_marks / total_max_marks) * 100
        else:
            percentage = 0
        
        return {
            'average_percentage': Decimal(str(percentage)),
            'number_of_assessments': scores.count(),
            'total_marks': sum([s.marks_obtained for s in scores]),
            'grade': get_grade(percentage)
        }
    
    @staticmethod
    def calculate_term_result(student, term, class_obj):
        """
        Calculate complete term results for a student
        """
        # Get all subject performances
        subject_performances = SubjectPerformance.objects.filter(
            student=student,
            term=term
        )
        
        if not subject_performances.exists():
            return None
        
        # Calculate totals
        total_marks = subject_performances.aggregate(Sum('total_marks'))['total_marks__sum'] or 0
        total_max_marks = subject_performances.aggregate(Sum('max_marks'))['max_marks__sum'] or 0
        
        if total_max_marks > 0:
            average_percentage = (total_marks / total_max_marks) * 100
        else:
            average_percentage = 0
        
        # Count passed/failed
        subjects_passed = subject_performances.filter(average_percentage__gte=50).count()
        subjects_failed = subject_performances.filter(average_percentage__lt=50).count()
        
        # Get rankings
        all_results = TermResult.objects.filter(term=term, class_obj=class_obj).order_by('-average_percentage')
        position = 1
        for idx, result in enumerate(all_results, 1):
            if result.student == student:
                position = idx
                break
        
        return {
            'total_marks': total_marks,
            'total_max_marks': total_max_marks,
            'average_percentage': Decimal(str(average_percentage)),
            'position_in_class': position,
            'overall_grade': get_grade(average_percentage),
            'subjects_passed': subjects_passed,
            'subjects_failed': subjects_failed,
            'status': determine_promotion_status(subjects_passed, subjects_failed)
        }
    
    @staticmethod
    def calculate_attendance_summary(student, class_obj, term):
        """
        Calculate attendance summary for a student in a term
        """
        attendance_records = Attendance.objects.filter(
            student=student,
            class_obj=class_obj,
            term=term
        )
        
        if not attendance_records.exists():
            return None
        
        total_school_days = attendance_records.count()
        total_present = attendance_records.filter(status='present').count()
        total_absent = attendance_records.filter(status='absent').count()
        total_late = attendance_records.filter(status='late').count()
        total_excused = attendance_records.filter(status='excused').count()
        
        if total_school_days > 0:
            attendance_percentage = (total_present / total_school_days) * 100
        else:
            attendance_percentage = 0
        
        return {
            'total_school_days': total_school_days,
            'total_present': total_present,
            'total_absent': total_absent,
            'total_late': total_late,
            'total_excused': total_excused,
            'attendance_percentage': Decimal(str(attendance_percentage))
        }
    
    @staticmethod
    def calculate_progress_trend(student, academic_year=None):
        """
        Determine if student is improving, declining, or stable
        """
        if academic_year:
            results = YearlyResult.objects.filter(
                student=student,
                academic_year=academic_year
            )
        else:
            results = YearlyResult.objects.filter(student=student).order_by('-academic_year')[:3]
        
        if results.count() < 2:
            return 'stable'
        
        results_list = list(results)
        first_avg = Decimal(str(results_list[0].annual_average or 0))
        last_avg = Decimal(str(results_list[-1].annual_average or 0))
        
        diff = last_avg - first_avg
        
        if diff > 5:
            return 'improving'
        elif diff < -5:
            return 'declining'
        else:
            return 'stable'


# ============== Grade Calculation ==============

def get_grade(percentage):
    """
    Convert percentage to letter grade
    """
    if percentage >= 90:
        return 'A'
    elif percentage >= 80:
        return 'B'
    elif percentage >= 70:
        return 'C'
    elif percentage >= 60:
        return 'D'
    elif percentage >= 50:
        return 'E'
    else:
        return 'F'


def determine_promotion_status(subjects_passed, subjects_failed):
    """
    Determine promotion status based on passed/failed subjects
    """
    if subjects_failed == 0:
        return 'promoted'
    elif subjects_failed == 1:
        return 'conditional'
    else:
        return 'retained'


# ============== Attendance Utilities ==============

class AttendanceUtils:
    """Utilities for attendance operations"""
    
    @staticmethod
    def mark_bulk_attendance(class_obj, date, attendance_data, term=None, teacher=None):
        """
        Mark attendance for multiple students
        attendance_data: List of {'student_id': ..., 'status': ...}
        """
        created = []
        errors = []
        
        if not term:
            term = Term.objects.filter(is_current=True).first()
        
        for data in attendance_data:
            try:
                student = Student.objects.get(id=data['student_id'])
                attendance, created_flag = Attendance.objects.update_or_create(
                    student=student,
                    class_obj=class_obj,
                    date=date,
                    defaults={
                        'status': data.get('status', 'absent'),
                        'remarks': data.get('remarks', ''),
                        'term': term,
                        'teacher': teacher
                    }
                )
                created.append({
                    'student': student.user.get_full_name(),
                    'status': attendance.get_status_display(),
                    'created': created_flag
                })
            except Student.DoesNotExist:
                errors.append(f"Student {data['student_id']} not found")
            except Exception as e:
                errors.append(f"Error processing {data['student_id']}: {str(e)}")
        
        return {'created': created, 'errors': errors}
    
    @staticmethod
    def generate_attendance_summary(class_obj, term):
        """
        Generate attendance summaries for all students in a class
        """
        students = class_obj.students.filter(is_active=True)
        summaries = []
        
        for student in students:
            summary_data = AcademicCalculations.calculate_attendance_summary(
                student, class_obj, term
            )
            
            if summary_data:
                summary, created = AttendanceSummary.objects.update_or_create(
                    student=student,
                    class_obj=class_obj,
                    term=term,
                    defaults=summary_data
                )
                summaries.append(summary)
        
        return summaries


# ============== Result Calculation ==============

class ResultCalculation:
    """Utilities for result calculations"""
    
    @staticmethod
    def generate_term_results(class_obj, term):
        """
        Generate term results for all students in a class
        """
        students = class_obj.students.filter(is_active=True)
        results = []
        
        for student in students:
            # Get all subject performances for this student and term
            subject_performances = SubjectPerformance.objects.filter(
                student=student,
                term=term
            )
            
            if not subject_performances.exists():
                continue
            
            # Calculate aggregates
            total_marks = sum([sp.total_marks for sp in subject_performances])
            total_max_marks = sum([sp.max_marks for sp in subject_performances])
            
            if total_max_marks > 0:
                average_percentage = (total_marks / total_max_marks) * 100
            else:
                average_percentage = 0
            
            subjects_passed = subject_performances.filter(average_percentage__gte=50).count()
            subjects_failed = subject_performances.filter(average_percentage__lt=50).count()
            best_subject = subject_performances.order_by('-average_percentage').first()
            worst_subject = subject_performances.order_by('average_percentage').first()
            
            # Create result
            term_result, created = TermResult.objects.update_or_create(
                student=student,
                term=term,
                class_obj=class_obj,
                defaults={
                    'total_marks': total_marks,
                    'total_max_marks': total_max_marks,
                    'average_percentage': Decimal(str(average_percentage)),
                    'overall_grade': get_grade(average_percentage),
                    'subjects_passed': subjects_passed,
                    'subjects_failed': subjects_failed,
                    'best_subject': best_subject.subject if best_subject else None,
                    'worst_subject': worst_subject.subject if worst_subject else None,
                    'status': determine_promotion_status(subjects_passed, subjects_failed),
                    'total_students_in_class': class_obj.get_student_count()
                }
            )
            results.append(term_result)
        
        # Update rankings
        ResultCalculation.update_class_rankings(class_obj, term, results)
        return results
    
    @staticmethod
    def update_class_rankings(class_obj, term, results):
        """
        Update position rankings for all students in class
        """
        sorted_results = sorted(results, key=lambda x: x.average_percentage, reverse=True)
        
        for position, result in enumerate(sorted_results, 1):
            result.position_in_class = position
            result.save(update_fields=['position_in_class'])
    
    @staticmethod
    def generate_yearly_results(student, academic_year):
        """
        Generate yearly summary for a student
        """
        terms = Term.objects.filter(academic_year=academic_year)
        
        yearly_result, created = YearlyResult.objects.update_or_create(
            student=student,
            academic_year=academic_year,
            defaults={'student': student}
        )
        
        term_results = []
        averages = []
        
        for term in terms:
            term_result = TermResult.objects.filter(
                student=student,
                term=term
            ).first()
            
            if term_result:
                term_results.append(term_result)
                averages.append(float(term_result.average_percentage or 0))
                
                if term.name == 'first':
                    yearly_result.term1_result = term_result
                elif term.name == 'second':
                    yearly_result.term2_result = term_result
                elif term.name == 'third':
                    yearly_result.term3_result = term_result
        
        # Calculate annual average
        if averages:
            yearly_result.annual_average = Decimal(str(sum(averages) / len(averages)))
        
        # Determine trend
        yearly_result.improvement_trend = AcademicCalculations.calculate_progress_trend(
            student, academic_year
        )
        
        yearly_result.save()
        return yearly_result


# ============== Django Management Commands ==============
# Place these in: apps/{app_name}/management/commands/{command_name}.py

"""
Example management command: python manage.py generate_term_results --term first --class "Form 1A"

# Create file: scores/management/commands/generate_term_results.py
"""

from django.core.management.base import BaseCommand
from classes.models import Class, Term
from datetime import date

class Command(BaseCommand):
    help = 'Generate term results for a specific class'
    
    def add_arguments(self, parser):
        parser.add_argument('--term', type=str, help='Term name (first, second, third)')
        parser.add_argument('--class', type=str, dest='class_name', help='Class name')
        parser.add_argument('--year', type=str, default=str(date.today().year), help='Academic year')
    
    def handle(self, *args, **options):
        term_name = options.get('term')
        class_name = options.get('class_name')
        year = options.get('year')
        
        try:
            term = Term.objects.get(name=term_name, academic_year=year)
            class_obj = Class.objects.get(name=class_name)
            
            results = ResultCalculation.generate_term_results(class_obj, term)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully generated results for {len(results)} students'
                )
            )
        except (Term.DoesNotExist, Class.DoesNotExist) as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )


"""
Example management command: python manage.py create_academic_year --year 2024/2025

# Create file: classes/management/commands/create_academic_year.py
"""

class CreateAcademicYearCommand(BaseCommand):
    help = 'Create academic year with three terms'
    
    def add_arguments(self, parser):
        parser.add_argument('--year', type=str, required=True, help='Academic year (e.g., 2024/2025)')
    
    def handle(self, *args, **options):
        year = options['year']
        
        terms_data = [
            {
                'name': 'first',
                'start_date': date(2024, 1, 15),
                'end_date': date(2024, 4, 15),
            },
            {
                'name': 'second',
                'start_date': date(2024, 4, 22),
                'end_date': date(2024, 8, 15),
            },
            {
                'name': 'third',
                'start_date': date(2024, 9, 2),
                'end_date': date(2024, 11, 29),
            },
        ]
        
        for term_data in terms_data:
            term_data['academic_year'] = year
            term, created = Term.objects.get_or_create(**term_data)
            status = 'Created' if created else 'Existing'
            self.stdout.write(f'{status}: {term.get_name_display()} {year}')


"""
Example management command: python manage.py cleanup_old_data --days 365

# Create file: users/management/commands/cleanup_old_data.py
"""

from django.utils import timezone
from datetime import timedelta

class CleanupOldDataCommand(BaseCommand):
    help = 'Clean up old/inactive data'
    
    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=365, help='Days to keep')
    
    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Delete old progress logs
        old_logs = ProgressLog.objects.filter(recorded_date__lt=cutoff_date)
        count = old_logs.count()
        old_logs.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Deleted {count} old progress logs')
        )
