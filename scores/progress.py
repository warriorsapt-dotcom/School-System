"""Longitudinal progress calculated from the student's saved term results."""

def student_progress(student):
    rows = []
    previous = None
    results = student.term_results.select_related('term', 'class_obj').order_by(
        'term__start_date', 'term__academic_year', 'class_obj__form_level', 'pk'
    )
    for result in results:
        average = float(result.average_percentage)
        rows.append({
            'id': str(result.pk), 'student': str(student.pk),
            'student_name': student.user.get_full_name(),
            'term': str(result.term_id), 'term_name': result.term.get_name_display(),
            'term_start': result.term.start_date.isoformat(),
            'academic_year': result.term.academic_year,
            'class_name': result.recorded_class_name or result.class_obj.name,
            'level': result.recorded_level or result.class_obj.form_level,
            'average_percentage': average, 'overall_grade': result.overall_grade,
            'rank_in_class': result.position_in_class,
            'total_students_in_class': result.total_students_in_class,
            'subjects_passed': result.subjects_passed, 'subjects_failed': result.subjects_failed,
            'change': round(average - previous, 2) if previous is not None else None,
            'status': result.status,
        })
        previous = average
    return rows
