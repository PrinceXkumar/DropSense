import pathlib

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

import pandas as pd

from students.models import Student


class Command(BaseCommand):
    help = "Import students from student_dataset.xlsx into the database."

    def handle(self, *args, **options):
        project_root = pathlib.Path(__file__).resolve().parents[3]
        excel_path = project_root / "student_dataset.xlsx"

        if not excel_path.exists():
            raise CommandError(f"Could not find {excel_path}. Place student_dataset.xlsx in the project root.")

        self.stdout.write(self.style.NOTICE(f"Reading data from {excel_path} ..."))

        df = pd.read_excel(excel_path)

        expected_columns = [
            "Marital status",
            "Application mode",
            "Application order",
            "Course",
            "Daytime/evening attendance",
            "Previous qualification",
            "Nacionality",
            "Mother's qualification",
            "Father's qualification",
            "Mother's occupation",
            "Father's occupation",
            "Displaced",
            "Educational special needs",
            "Debtor",
            "Tuition fees up to date",
            "Gender",
            "Scholarship holder",
            "Age at enrollment",
            "International",
            "Curricular units 1st sem (credited)",
            "Curricular units 1st sem (enrolled)",
            "Curricular units 1st sem (evaluations)",
            "Curricular units 1st sem (approved)",
            "Curricular units 1st sem (grade)",
            "Curricular units 1st sem (without evaluations)",
            "Curricular units 2nd sem (credited)",
            "Curricular units 2nd sem (enrolled)",
            "Curricular units 2nd sem (evaluations)",
            "Curricular units 2nd sem (approved)",
            "Curricular units 2nd sem (grade)",
            "Curricular units 2nd sem (without evaluations)",
            "Unemployment rate",
            "Inflation rate",
            "GDP",
            "Target",
        ]

        missing = [c for c in expected_columns if c not in df.columns]
        if missing:
            raise CommandError(f"Missing expected columns in Excel file: {missing}")

        # Normalize boolean-like columns
        bool_cols = [
            "Displaced",
            "Educational special needs",
            "Debtor",
            "Tuition fees up to date",
            "Scholarship holder",
            "International",
        ]

        for col in bool_cols:
            df[col] = df[col].astype(str).str.strip().str.lower().map(
                {"1": True, "yes": True, "true": True, "0": False, "no": False, "false": False}
            )

        created_count = 0

        with transaction.atomic():
            Student.objects.all().delete()

            for _, row in df.iterrows():
                Student.objects.create(
                    marital_status=row["Marital status"],
                    application_mode=row["Application mode"],
                    application_order=int(row["Application order"]),
                    course=row["Course"],
                    daytime_evening_attendance=row["Daytime/evening attendance"],
                    previous_qualification=row["Previous qualification"],
                    nacionality=row["Nacionality"],
                    mother_qualification=row["Mother's qualification"],
                    father_qualification=row["Father's qualification"],
                    mother_occupation=row["Mother's occupation"],
                    father_occupation=row["Father's occupation"],
                    displaced=bool(row["Displaced"]),
                    educational_special_needs=bool(row["Educational special needs"]),
                    debtor=bool(row["Debtor"]),
                    tuition_fees_up_to_date=bool(row["Tuition fees up to date"]),
                    gender=row["Gender"],
                    scholarship_holder=bool(row["Scholarship holder"]),
                    age_at_enrollment=int(row["Age at enrollment"]),
                    international=bool(row["International"]),
                    curricular_units_1st_sem_credited=int(row["Curricular units 1st sem (credited)"]),
                    curricular_units_1st_sem_enrolled=int(row["Curricular units 1st sem (enrolled)"]),
                    curricular_units_1st_sem_evaluations=int(row["Curricular units 1st sem (evaluations)"]),
                    curricular_units_1st_sem_approved=int(row["Curricular units 1st sem (approved)"]),
                    curricular_units_1st_sem_grade=float(row["Curricular units 1st sem (grade)"]),
                    curricular_units_1st_sem_without_evaluations=int(
                        row["Curricular units 1st sem (without evaluations)"]
                    ),
                    curricular_units_2nd_sem_credited=int(row["Curricular units 2nd sem (credited)"]),
                    curricular_units_2nd_sem_enrolled=int(row["Curricular units 2nd sem (enrolled)"]),
                    curricular_units_2nd_sem_evaluations=int(row["Curricular units 2nd sem (evaluations)"]),
                    curricular_units_2nd_sem_approved=int(row["Curricular units 2nd sem (approved)"]),
                    curricular_units_2nd_sem_grade=float(row["Curricular units 2nd sem (grade)"]),
                    curricular_units_2nd_sem_without_evaluations=int(
                        row["Curricular units 2nd sem (without evaluations)"]
                    ),
                    unemployment_rate=float(row["Unemployment rate"]),
                    inflation_rate=float(row["Inflation rate"]),
                    gdp=float(row["GDP"]),
                    target=str(row.get("Target", "")),
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {created_count} students."))

