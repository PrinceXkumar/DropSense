import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse

from .models import Student
from .risk_engine import calculate_risk
from .ml_predictor import predict_student, get_feature_importances, get_student_feature_contributions
from .report_generator import generate_risk_report_pdf


def home(request):
    """Public landing page."""
    return render(request, "home.html")


# ── helpers ─────────────────────────────────────────────────────

def _base_qs(user):
    """Return the student queryset appropriate for *user*'s role."""
    # 1. Mentors see only their assigned students
    if hasattr(user, "is_mentor") and user.is_mentor():
        return Student.objects.filter(mentor=user)
    # 2. Admins/Superusers see everything (if not a mentor)
    if hasattr(user, "is_admin") and user.is_admin():
        return Student.objects.all()
    # 3. Parents see only their children
    if hasattr(user, "is_parent") and user.is_parent():
        return Student.objects.filter(parent=user)
    return Student.objects.none()


def _check_student_access(user, student):
    """Raise PermissionDenied if *user* may not view *student*."""
    # 1. Mentor check (Priority)
    if hasattr(user, "is_mentor") and user.is_mentor():
        if student.mentor_id == user.id:
            return
        raise PermissionDenied("You are assigned as a Mentor but this is not your student.")
    
    # 2. Admin/Superuser check
    if hasattr(user, "is_admin") and user.is_admin():
        return

    # 3. Parent check
    if hasattr(user, "is_parent") and user.is_parent() and student.parent_id == user.id:
        return
    raise PermissionDenied("You are not allowed to view this student.")


# ── Student list ────────────────────────────────────────────────

@login_required
def student_list(request):
    user = request.user
    students_qs = _base_qs(user).order_by("id")

    # ── Search & filter ──
    search = request.GET.get("q", "").strip()
    course_filter = request.GET.get("course", "").strip()
    risk_filter = request.GET.get("risk", "").strip()
    target_filter = request.GET.get("target", "").strip()

    if search:
        students_qs = students_qs.filter(
            Q(course__icontains=search)
            | Q(nacionality__icontains=search)
            | Q(id__icontains=search)
        )
    if course_filter:
        students_qs = students_qs.filter(course=course_filter)
    if target_filter:
        students_qs = students_qs.filter(target=target_filter)

    # Attach risk to each student (for badge + optional filtering)
    students_with_risk = []
    for s in students_qs:
        r = calculate_risk(s)
        s.risk = r
        if risk_filter and r["risk_level"].lower() != risk_filter.lower():
            continue
        students_with_risk.append(s)

    # Available courses for filter dropdown
    all_courses = (
        _base_qs(user)
        .values_list("course", flat=True)
        .distinct()
        .order_by("course")
    )

    paginator = Paginator(students_with_risk, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "students/student_list.html",
        {
            "page_obj": page_obj,
            "search": search,
            "course_filter": course_filter,
            "risk_filter": risk_filter,
            "target_filter": target_filter,
            "all_courses": all_courses,
        },
    )


# ── Student detail ──────────────────────────────────────────────

@login_required
def student_detail(request, pk: int):
    student = get_object_or_404(Student, pk=pk)
    _check_student_access(request.user, student)

    risk = calculate_risk(student)
    ml = predict_student(student)

    return render(
        request,
        "students/student_detail.html",
        {"student": student, "risk": risk, "ml": ml},
    )


# ── Risk report ─────────────────────────────────────────────────

@login_required
def student_risk_report(request, pk: int):
    student = get_object_or_404(Student, pk=pk)
    _check_student_access(request.user, student)

    risk = calculate_risk(student)

    # SVG gauge: circumference = 2 * pi * 65 ≈ 408.4
    circumference = 408.4
    risk_gauge_offset = circumference - (risk["risk_score"] / 100) * circumference

    ml = predict_student(student)
    contributions = get_student_feature_contributions(student, top_n=8)
    importances = get_feature_importances(top_n=10)

    context = {
        "student": student,
        "risk": risk,
        "risk_gauge_offset": risk_gauge_offset,
        "ml": ml,
        "contributions": contributions,
        "importances": importances,
    }
    return render(request, "students/risk_report.html", context)


@login_required
def export_risk_report(request, pk: int):
    student = get_object_or_404(Student, pk=pk)
    _check_student_access(request.user, student)

    risk = calculate_risk(student)
    ml = predict_student(student)
    contributions = get_student_feature_contributions(student, top_n=8)

    pdf_buffer = generate_risk_report_pdf(student, risk, ml, contributions)

    response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="risk_report_student_{student.pk}.pdf"'
    return response

# ── Analytics dashboard ────────────────────────────────────────

@login_required
def analytics_dashboard(request):
    user = request.user
    if not (
        (hasattr(user, "is_admin") and user.is_admin())
        or (hasattr(user, "is_mentor") and user.is_mentor())
        or (hasattr(user, "is_parent") and user.is_parent())
    ):
        raise PermissionDenied("Analytics is restricted to admins, mentors, and parents.")

    qs = _base_qs(user)
    total = qs.count()

    # Gender distribution
    gender_data = list(qs.values("gender").annotate(count=Count("id")).order_by("gender"))

    # Course-wise (top 10)
    course_data = list(
        qs.values("course").annotate(count=Count("id")).order_by("-count")[:10]
    )

    # Average grades
    avg_grades = qs.aggregate(
        avg_sem1=Avg("curricular_units_1st_sem_grade"),
        avg_sem2=Avg("curricular_units_2nd_sem_grade"),
    )

    # Fee status
    fee_data = {
        "up_to_date": qs.filter(tuition_fees_up_to_date=True).count(),
        "not_up_to_date": qs.filter(tuition_fees_up_to_date=False).count(),
    }

    # Scholarship
    scholarship_data = {
        "holders": qs.filter(scholarship_holder=True).count(),
        "non_holders": qs.filter(scholarship_holder=False).count(),
    }

    # Debtor
    debtor_data = {
        "debtors": qs.filter(debtor=True).count(),
        "non_debtors": qs.filter(debtor=False).count(),
    }

    # Age bins
    age_bins = [
        ("17-20", 17, 20),
        ("21-25", 21, 25),
        ("26-30", 26, 30),
        ("31-40", 31, 40),
        ("40+", 41, 100),
    ]
    age_data = [
        {"label": label, "count": qs.filter(age_at_enrollment__gte=lo, age_at_enrollment__lte=hi).count()}
        for label, lo, hi in age_bins
    ]

    # Target / outcome distribution
    target_data = list(
        qs.exclude(target="").values("target").annotate(count=Count("id")).order_by("target")
    )

    # Risk distribution
    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    for s in qs.iterator():
        r = calculate_risk(s)
        risk_counts[r["risk_level"]] += 1

    # Approved units average
    approved_avg = qs.aggregate(
        avg_approved_sem1=Avg("curricular_units_1st_sem_approved"),
        avg_approved_sem2=Avg("curricular_units_2nd_sem_approved"),
    )

    context = {
        "total_students": total,
        "gender_data": json.dumps(gender_data),
        "course_data": json.dumps(course_data),
        "avg_grades": avg_grades,
        "fee_data": json.dumps(fee_data),
        "scholarship_data": json.dumps(scholarship_data),
        "debtor_data": json.dumps(debtor_data),
        "age_data": json.dumps(age_data),
        "target_data": json.dumps(target_data),
        "risk_counts": json.dumps(risk_counts),
        "approved_avg": approved_avg,
    }
    return render(request, "students/analytics.html", context)


@login_required
def parent_dashboard(request):
    """Dashboard specifically designed for parents to track their children."""
    user = request.user
    
    # Check if user has parent role (if custom method exists) or just filter by parent field
    students = Student.objects.filter(parent=user)
    
    student_data = []
    
    for s in students:
        risk = calculate_risk(s)
        ml = predict_student(s)
        
        # Determine color for risk
        risk_color = "red" if risk['risk_level'] == "High" else "yellow" if risk['risk_level'] == "Medium" else "green"
        
        # Recommendations logic
        recommendations = []
        if s.curricular_units_1st_sem_grade < 10 or s.curricular_units_2nd_sem_grade < 10:
            recommendations.append("Prioritize academic support and tutoring for low-grade subjects.")
        if s.curricular_units_2nd_sem_approved < (s.curricular_units_2nd_sem_enrolled / 2):
            recommendations.append("Consult with academic advisors regarding low subject approval rates.")
        if not s.tuition_fees_up_to_date:
            recommendations.append("Arrange tuition fee payments to maintain enrollment eligibility.")
        if s.debtor:
            recommendations.append("Schedule a financial aid consultation to manage outstanding debt.")
        if s.scholarship_holder and (s.curricular_units_2nd_sem_grade < 12):
            recommendations.append("Improve grades to ensure continued eligibility for scholarship benefits.")
        
        if not recommendations:
            recommendations.append("Academic status is excellent. Continue current study habits.")

        # Alerts
        alerts = []
        if risk['risk_level'] == "High":
            alerts.append("CRITICAL: High dropout risk detected. Immediate mentor intervention advised.")
        if not s.tuition_fees_up_to_date:
            alerts.append("FINANCIAL: Tuition fees are overdue for the current semester.")
            
        student_data.append({
            "student": s,
            "risk": risk,
            "risk_color": risk_color,
            "ml": ml,
            "recommendations": recommendations,
            "alerts": alerts,
        })

    return render(request, "students/parent_dashboard.html", {
        "student_data": student_data,
        "total_children": students.count(),
    })
