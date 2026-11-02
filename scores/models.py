from django.db import models
from django.core.validators import MinValueValidator
import uuid


class Score(models.Model):
    ASSESSMENT_TYPES = (
        ('test', 'Test'),
        ('exam', 'Examination'),
        ('assignment', 'Assignment'),
        ('project', 'Project'),
        ('class_work', 'Class Work'),
        ('homework', 'Home Work'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='scores')
    class_subject = models.ForeignKey('classes.ClassSubject', on_delete=models.CASCADE, related_name='scores')
    subject = models.ForeignKey('classes.Subject', on_delete=models.CASCADE, related_name='student_scores')
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100, validators=[MinValueValidator(0.01)])
    percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    term = models.ForeignKey('classes.Term', on_delete=models.SET_NULL, null=True)
    date_recorded = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.max_marks and self.max_marks > 0:
            self.percentage = (self.marks_obtained / self.max_marks) * 100
        super().save(*args, **kwargs)

    def get_grade(self):
        if self.percentage is None:
            return 'N/A'
        pct = float(self.percentage)
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

    def __str__(self):
        return f"{self.student} - {self.subject.name} ({self.assessment_type}): {self.marks_obtained}/{self.max_marks}"

    class Meta:
        ordering = ['-date_recorded']
        verbose_name = 'Score'
        verbose_name_plural = 'Scores'
        indexes = [
            models.Index(fields=['student', 'term']),
            models.Index(fields=['class_subject']),
        ]


class ScoreComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    score = models.ForeignKey(Score, on_delete=models.CASCADE, related_name='comments')
    teacher = models.ForeignKey('users.Teacher', on_delete=models.SET_NULL, null=True, related_name='score_comments')
    comment_text = models.TextField()
    comment_type = models.CharField(
        max_length=20,
        choices=[('positive', 'Positive'), ('constructive', 'Constructive'), ('neutral', 'Neutral')],
        default='neutral'
    )
    is_visible_to_student = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment on {self.score} by {self.teacher}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Score Comment'
        verbose_name_plural = 'Score Comments'


class SubjectPerformance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='subject_performances')
    subject = models.ForeignKey('classes.Subject', on_delete=models.CASCADE)
    term = models.ForeignKey('classes.Term', on_delete=models.CASCADE)
    total_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    max_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    average_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    number_of_assessments = models.IntegerField(default=0)
    grade = models.CharField(max_length=2, blank=True)
    rank_in_class = models.IntegerField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    calculated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.subject.name} ({self.term})"

    class Meta:
        unique_together = ('student', 'subject', 'term')
        verbose_name = 'Subject Performance'
        verbose_name_plural = 'Subject Performances'


class TermResult(models.Model):
    RESULT_STATUS = (
        ('promoted', 'Promoted'),
        ('retained', 'Retained'),
        ('conditional', 'Conditional Promotion'),
        ('pending', 'Pending'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='term_results')
    term = models.ForeignKey('classes.Term', on_delete=models.CASCADE, related_name='results')
    class_obj = models.ForeignKey('classes.Class', on_delete=models.CASCADE)

    total_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_max_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    average_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    position_in_class = models.IntegerField(blank=True, null=True)
    total_students_in_class = models.IntegerField(default=0)
    overall_grade = models.CharField(max_length=2, blank=True)

    subjects_passed = models.IntegerField(default=0)
    subjects_failed = models.IntegerField(default=0)
    best_subject = models.ForeignKey('classes.Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    worst_subject = models.ForeignKey('classes.Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    status = models.CharField(max_length=20, choices=RESULT_STATUS, default='pending')
    principal_comment = models.TextField(blank=True, null=True)
    class_teacher_comment = models.TextField(blank=True, null=True)

    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_results')
    approval_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.term}"

    def get_overall_grade(self):
        avg = float(self.average_percentage)
        if avg >= 90:
            return 'A'
        elif avg >= 80:
            return 'B'
        elif avg >= 70:
            return 'C'
        elif avg >= 60:
            return 'D'
        elif avg >= 50:
            return 'E'
        else:
            return 'F'

    class Meta:
        unique_together = ('student', 'term', 'class_obj')
        ordering = ['-term']
        verbose_name = 'Term Result'
        verbose_name_plural = 'Term Results'
        indexes = [
            models.Index(fields=['student', 'term']),
        ]


class YearlyResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='yearly_results')
    academic_year = models.CharField(max_length=9)

    term1_result = models.ForeignKey(TermResult, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', limit_choices_to={'term__name': 'first'})
    term2_result = models.ForeignKey(TermResult, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', limit_choices_to={'term__name': 'second'})
    term3_result = models.ForeignKey(TermResult, on_delete=models.SET_NULL, null=True, blank=True, related_name='+', limit_choices_to={'term__name': 'third'})

    annual_average = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    improvement_trend = models.CharField(
        max_length=20,
        choices=[('improving', 'Improving'), ('declining', 'Declining'), ('stable', 'Stable')],
        blank=True
    )
    principal_remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.academic_year}"

    class Meta:
        unique_together = ('student', 'academic_year')
        ordering = ['-academic_year']
        verbose_name = 'Yearly Result'
        verbose_name_plural = 'Yearly Results'


class ProgressLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='progress_logs')
    term = models.ForeignKey('classes.Term', on_delete=models.SET_NULL, null=True)
    academic_year = models.CharField(max_length=9)

    average_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    rank_in_class = models.IntegerField(blank=True, null=True)
    subjects_passed = models.IntegerField(default=0)
    subjects_failed = models.IntegerField(default=0)
    improvement_flag = models.CharField(
        max_length=20,
        choices=[('high', 'High Performer'), ('average', 'Average'), ('at_risk', 'At Risk')],
        default='average'
    )
    notes = models.TextField(blank=True, null=True)
    recorded_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.term}"

    class Meta:
        ordering = ['-recorded_date']
        verbose_name = 'Progress Log'
        verbose_name_plural = 'Progress Logs'
