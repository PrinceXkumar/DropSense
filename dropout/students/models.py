from django.conf import settings
from django.db import models


class Student(models.Model):
    # Demographic / background info
    marital_status = models.CharField(max_length=100)
    application_mode = models.CharField(max_length=100)
    application_order = models.IntegerField()
    course = models.CharField(max_length=255)
    daytime_evening_attendance = models.CharField(max_length=50)
    previous_qualification = models.CharField(max_length=255)
    nacionality = models.CharField(max_length=100)
    mother_qualification = models.CharField(max_length=255)
    father_qualification = models.CharField(max_length=255)
    mother_occupation = models.CharField(max_length=255)
    father_occupation = models.CharField(max_length=255)
    displaced = models.BooleanField()
    educational_special_needs = models.BooleanField()
    debtor = models.BooleanField()
    tuition_fees_up_to_date = models.BooleanField()
    gender = models.CharField(max_length=10)
    scholarship_holder = models.BooleanField()
    age_at_enrollment = models.IntegerField()
    international = models.BooleanField()

    # Academic Performance (Semester 1)
    curricular_units_1st_sem_credited = models.IntegerField()
    curricular_units_1st_sem_enrolled = models.IntegerField()
    curricular_units_1st_sem_evaluations = models.IntegerField()
    curricular_units_1st_sem_approved = models.IntegerField()
    curricular_units_1st_sem_grade = models.FloatField()
    curricular_units_1st_sem_without_evaluations = models.IntegerField()

    # Academic Performance (Semester 2)
    curricular_units_2nd_sem_credited = models.IntegerField()
    curricular_units_2nd_sem_enrolled = models.IntegerField()
    curricular_units_2nd_sem_evaluations = models.IntegerField()
    curricular_units_2nd_sem_approved = models.IntegerField()
    curricular_units_2nd_sem_grade = models.FloatField()
    curricular_units_2nd_sem_without_evaluations = models.IntegerField()

    # Economic indicators
    unemployment_rate = models.FloatField()
    inflation_rate = models.FloatField()
    gdp = models.FloatField()

    # Target / outcome
    TARGET_CHOICES = [
        ('Dropout', 'Dropout'),
        ('Graduate', 'Graduate'),
        ('Enrolled', 'Enrolled'),
    ]
    target = models.CharField(
        max_length=20, choices=TARGET_CHOICES, blank=True, default=''
    )

    # Relationships
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_students",
    )
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )

    def __str__(self) -> str:
        return f"Student #{self.pk} - {self.course}"
