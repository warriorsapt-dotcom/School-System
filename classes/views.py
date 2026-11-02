from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Class, Subject, ClassSubject, Term
from .serializers import ClassSerializer, ClassDetailSerializer, SubjectSerializer, TermSerializer
from attendance.serializers import AttendanceSerializer
from users.views import IsAdmin


class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.select_related('class_teacher__user').all()
    serializer_class = ClassSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['form_level', 'is_active']
    search_fields = ['name', 'stream']
    ordering_fields = ['form_level', 'section']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClassDetailSerializer
        return ClassSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def attendance(self, request, pk=None):
        from attendance.models import Attendance
        class_obj = self.get_object()
        records = Attendance.objects.filter(class_obj=class_obj)
        return Response(AttendanceSerializer(records, many=True).data)

    @action(detail=True, methods=['get'])
    def student_performance(self, request, pk=None):
        from scores.models import Score, TermResult
        from attendance.models import Attendance
        from django.db.models import Count

        cls = self.get_object()

        # Only the class teacher of this class or an admin may access this
        if request.user.role != 'admin':
            try:
                teacher = request.user.teacher_profile
                if cls.class_teacher_id != teacher.id:
                    return Response(
                        {'error': 'You are not the class teacher for this class.'},
                        status=403
                    )
            except Exception:
                return Response({'error': 'Access denied.'}, status=403)

        current_term = Term.objects.filter(is_current=True).first()
        students = cls.students.filter(is_active=True).select_related('user').order_by('user__last_name', 'user__first_name')

        # Bulk-fetch scores for this class / term to avoid N+1
        score_filter = {'class_subject__class_obj': cls}
        if current_term:
            score_filter['term'] = current_term
        all_scores = Score.objects.filter(**score_filter).select_related('student', 'subject')

        score_map = {}  # { student_id: { subject_name: {sum, count} } }
        for score in all_scores:
            sid = str(score.student_id)
            subj = score.subject.name
            score_map.setdefault(sid, {}).setdefault(subj, {'sum': 0, 'count': 0})
            score_map[sid][subj]['sum'] += float(score.percentage or 0)
            score_map[sid][subj]['count'] += 1

        # Bulk-fetch term results
        tr_filter = {'class_obj': cls}
        if current_term:
            tr_filter['term'] = current_term
        all_results = {str(tr.student_id): tr for tr in TermResult.objects.filter(**tr_filter)}

        # Bulk-fetch attendance counts
        att_filter = {'class_obj': cls}
        if current_term:
            att_filter['term'] = current_term
        att_rows = (
            Attendance.objects.filter(**att_filter)
            .values('student_id', 'status')
            .annotate(n=Count('id'))
        )
        att_map = {}  # { student_id: { status: count } }
        for row in att_rows:
            sid = str(row['student_id'])
            att_map.setdefault(sid, {})[row['status']] = row['n']

        student_data = []
        for student in students:
            sid = str(student.id)

            # Subject averages from raw scores
            subj_raw = score_map.get(sid, {})
            subject_avgs = {
                k: round(v['sum'] / v['count'], 1)
                for k, v in subj_raw.items()
            }

            # Term result (preferred) or computed average
            tr = all_results.get(sid)
            average_pct  = float(tr.average_percentage) if tr else (
                round(sum(subject_avgs.values()) / len(subject_avgs), 1) if subject_avgs else 0
            )
            overall_grade = tr.overall_grade if tr else '—'
            position      = tr.position_in_class if tr else None
            status        = tr.status if tr else 'pending'
            subj_passed   = tr.subjects_passed if tr else None
            subj_failed   = tr.subjects_failed if tr else None

            # Attendance
            att = att_map.get(sid, {})
            att_total   = sum(att.values())
            att_present = att.get('present', 0)
            att_rate    = round(att_present / att_total * 100, 1) if att_total else 0

            student_data.append({
                'student_id':       sid,
                'student_name':     student.user.get_full_name(),
                'admission_number': student.admission_number,
                'average_percentage': average_pct,
                'overall_grade':    overall_grade,
                'position_in_class': position,
                'subjects_passed':  subj_passed,
                'subjects_failed':  subj_failed,
                'status':           status,
                'attendance_rate':  att_rate,
                'attendance_present': att_present,
                'attendance_total': att_total,
                'subjects':         subject_avgs,
            })

        # Sort by position if available, else by average descending
        student_data.sort(key=lambda x: (x['position_in_class'] or 9999, -x['average_percentage']))

        # Collect all subject names across the class
        all_subjects = sorted({s for row in student_data for s in row['subjects']})

        return Response({
            'class_name':     cls.name,
            'form_level':     cls.form_level,
            'section':        cls.section,
            'total_students': len(student_data),
            'current_term':   str(current_term) if current_term else None,
            'all_subjects':   all_subjects,
            'students':       student_data,
        })


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'code']
    ordering_fields = ['name']


class TermViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Term.objects.all()
    serializer_class = TermSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['academic_year', 'is_current']
    ordering_fields = ['-academic_year', 'name']
