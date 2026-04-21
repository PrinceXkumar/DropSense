from django.urls import path

from . import views

app_name = "students"

urlpatterns = [
    path("", views.home, name="home"),
    path("students/", views.student_list, name="student_list"),
    path("students/<int:pk>/", views.student_detail, name="student_detail"),
    path("students/<int:pk>/risk-report/", views.student_risk_report, name="risk_report"),
    path("students/<int:pk>/export/", views.export_risk_report, name="export_risk_report"),
    path("analytics/", views.analytics_dashboard, name="analytics"),
    path("parent/dashboard/", views.parent_dashboard, name="parent_dashboard"),
]
