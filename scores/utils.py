from decimal import Decimal
from django.db.models import Avg, Sum, Q
from datetime import date

from scores.models import Score, TermResult, YearlyResult, ProgressLog, SubjectPerformance
from attendance.models import Attendance, AttendanceSummary
from classes.models import Term, Class
from users.models import Student


def get_grade(percentage):
    pct = float(percentage)
    if pct >= 90:
        return 'A'
    elif pct >= 80:
        return 'B'
    elif pct >= 70:
        return 'C'
    elif pct >= 60:
        return 'D'
    elif pct >= 50:
        return 'E'
    else:
        return 'F'


def determine_promotion_status(subjects_passed, subjects_failed):
    if subjects_failed == 0:
        return 'promoted'
    elif subjects_failed == 1:
        return 'conditional'
    else:
        return 'retained'


class AcademicCalculations:

    @staticmethod
    def calculate_subject_performance(student, subject, term):
        scores = Score.objects.filter(student=student, subject=subject, term=term, is_approved=True)
        if not scores.exists():
            return None

        agg = scores.aggregate(avg_obtained=Avg('marks_obtained'), avg_max=Avg('max_marks'))
        avg_obtained = agg['avg_obtained'] or 0
        avg_max = agg['avg_max'] or 0
        percentage = (avg_obtained / avg_max * 100) if avg_max > 0 else 0

        return {
            'average_percentage': Decimal(str(percentage)),
            'number_of_assessments': scores.count(),
            'total_marks': sum(s.marks_obtained for s in scores),
            'grade': get_grade(percentage),
        }

    @staticmethod
    def calculate_term_result(student, term, class_obj):
        subject_performances = SubjectPerformance.objects.filter(student=student, term=term)
        if not subject_performances.exists():
            return None

        agg = subject_performances.aggregate(
            total_marks=Sum('total_marks'),
            total_max_marks=Sum('max_marks'),
        )
        total_marks = agg['total_marks'] or 0
        total_max_marks = agg['total_max_marks'] or 0
        average_percentage = (total_marks / total_max_marks * 100) if total_max_marks > 0 else 0

        subjects_passed = subject_performances.filter(average_percentage__gte=50).count()
        subjects_failed = subject_performances.filter(average_percentage__lt=50).count()

        all_results = TermResult.objects.filter(term=term, class_obj=class_obj).order_by('-average_percentage')
        position = next(
            (idx for idx, r in enumerate(all_results, 1) if r.student == student),
            1
        )

        return {
            'total_marks': total_marks,
            'total_max_marks': total_max_marks,
            'average_percentage': Decimal(str(average_percentage)),
            'position_in_class': position,
            'overall_grade': get_grade(average_percentage),
            'subjects_passed': subjects_passed,
            'subjects_failed': subjects_failed,
            'status': determine_promotion_status(subjects_passed, subjects_failed),
        }

    @staticmethod
    def calculate_attendance_summary(student, class_obj, term):
        records = Attendance.objects.filter(student=student, class_obj=class_obj, term=term)
        if not records.exists():
            return None

        total = records.count()
        present = records.filter(status='present').count()
        absent = records.filter(status='absent').count()
        late = records.filter(status='late').count()
        excused = records.filter(status='excused').count()
        percentage = (present / total * 100) if total > 0 else 0

        return {
            'total_school_days': total,
            'total_present': present,
            'total_absent': absent,
            'total_late': late,
            'total_excused': excused,
            'attendance_percentage': Decimal(str(percentage)),
        }

    @staticmethod
    def calculate_progress_trend(student, academic_year=None):
        qs = YearlyResult.objects.filter(student=student)
        if academic_year:
            qs = qs.filter(academic_year=academic_year)
        else:
            qs = qs.order_by('-academic_year')[:3]

        results = list(qs)
        if len(results) < 2:
            return 'stable'

        diff = Decimal(str(results[-1].annual_average or 0)) - Decimal(str(results[0].annual_average or 0))
        if diff > 5:
            return 'improving'
        elif diff < -5:
            return 'declining'
        return 'stable'


class AttendanceUtils:

    @staticmethod
    def mark_bulk_attendance(class_obj, attendance_date, attendance_data, term=None, teacher=None):
        if not term:
            term = Term.objects.filter(is_current=True).first()

        created = []
        errors = []
        for data in attendance_data:
            try:
                student = Student.objects.get(id=data['student_id'])
                attendance, was_created = Attendance.objects.update_or_create(
                    student=student,
                    class_obj=class_obj,
                    date=attendance_date,
                    defaults={
                        'status': data.get('status', 'absent'),
                        'remarks': data.get('remarks', ''),
                        'term': term,
                        'teacher': teacher,
                    }
                )
                created.append({
                    'student': student.user.get_full_name(),
                    'status': attendance.get_status_display(),
                    'created': was_created,
                })
            except Student.DoesNotExist:
                errors.append(f"Student {data['student_id']} not found")
            except Exception as e:
                errors.append(f"Error processing {data['student_id']}: {str(e)}")

        return {'created': created, 'errors': errors}

    @staticmethod
    def generate_attendance_summary(class_obj, term):
        summaries = []
        for student in class_obj.students.filter(is_active=True):
            summary_data = AcademicCalculations.calculate_attendance_summary(student, class_obj, term)
            if summary_data:
                summary, _ = AttendanceSummary.objects.update_or_create(
                    student=student, class_obj=class_obj, term=term, defaults=summary_data
                )
                summaries.append(summary)
        return summaries


class ResultCalculation:

    @staticmethod
    def generate_term_results(class_obj, term):
        results = []
        for student in class_obj.students.filter(is_active=True):
            subject_performances = SubjectPerformance.objects.filter(student=student, term=term)
            if not subject_performances.exists():
                continue

            total_marks = sum(sp.total_marks for sp in subject_performances)
            total_max_marks = sum(sp.max_marks for sp in subject_performances)
            average_percentage = (total_marks / total_max_marks * 100) if total_max_marks > 0 else 0

            subjects_passed = subject_performances.filter(average_percentage__gte=50).count()
            subjects_failed = subject_performances.filter(average_percentage__lt=50).count()
            best = subject_performances.order_by('-average_percentage').first()
            worst = subject_performances.order_by('average_percentage').first()

            term_result, _ = TermResult.objects.update_or_create(
                student=student, term=term, class_obj=class_obj,
                defaults={
                    'total_marks': total_marks,
                    'total_max_marks': total_max_marks,
                    'average_percentage': Decimal(str(average_percentage)),
                    'overall_grade': get_grade(average_percentage),
                    'subjects_passed': subjects_passed,
                    'subjects_failed': subjects_failed,
                    'best_subject': best.subject if best else None,
                    'worst_subject': worst.subject if worst else None,
                    'status': determine_promotion_status(subjects_passed, subjects_failed),
                    'total_students_in_class': class_obj.get_student_count(),
                }
            )
            results.append(term_result)

        ResultCalculation.update_class_rankings(class_obj, term, results)
        return results

    @staticmethod
    def update_class_rankings(class_obj, term, results):
        for position, result in enumerate(sorted(results, key=lambda x: x.average_percentage, reverse=True), 1):
            result.position_in_class = position
            result.save(update_fields=['position_in_class'])

    @staticmethod
    def generate_yearly_results(student, academic_year):
        yearly_result, _ = YearlyResult.objects.update_or_create(
            student=student, academic_year=academic_year, defaults={'student': student}
        )

        averages = []
        for term in Term.objects.filter(academic_year=academic_year):
            term_result = TermResult.objects.filter(student=student, term=term).first()
            if term_result:
                averages.append(float(term_result.average_percentage or 0))
                if term.name == 'first':
                    yearly_result.term1_result = term_result
                elif term.name == 'second':
                    yearly_result.term2_result = term_result
                elif term.name == 'third':
                    yearly_result.term3_result = term_result

        if averages:
            yearly_result.annual_average = Decimal(str(sum(averages) / len(averages)))

        yearly_result.improvement_trend = AcademicCalculations.calculate_progress_trend(student, academic_year)
        yearly_result.save()
        return yearly_result
