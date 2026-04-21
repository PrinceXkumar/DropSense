import os
import joblib
import numpy as np
import pandas as pd

from django.conf import settings
from django.core.management.base import BaseCommand

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, f1_score
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder
from imblearn.over_sampling import SMOTE

from students.models import Student


# Features used for prediction (Refined set)
FEATURE_FIELDS = [
    "daytime_evening_attendance",
    "displaced",
    "educational_special_needs",
    "debtor",
    "tuition_fees_up_to_date",
    "gender",
    "scholarship_holder",
    "age_at_enrollment",
    "international",
    "curricular_units_1st_sem_credited",
    "curricular_units_1st_sem_enrolled",
    "curricular_units_1st_sem_evaluations",
    "curricular_units_1st_sem_approved",
    "curricular_units_1st_sem_grade",
    "curricular_units_1st_sem_without_evaluations",
    "curricular_units_2nd_sem_credited",
    "curricular_units_2nd_sem_enrolled",
    "curricular_units_2nd_sem_evaluations",
    "curricular_units_2nd_sem_approved",
    "curricular_units_2nd_sem_grade",
    "curricular_units_2nd_sem_without_evaluations",
    "unemployment_rate",
    "inflation_rate",
    "gdp",
]

# Identify categorical columns (usually strings in the Model)
CATEGORICAL_FIELDS = [
    "daytime_evening_attendance",
    "gender"
]

# Directory to save model artifacts
MODEL_DIR = os.path.join(settings.BASE_DIR, "ml_models")


class Command(BaseCommand):
    help = "Train a Random Forest model with robust preprocessing and evaluation."

    def add_arguments(self, parser):
        parser.add_argument("--estimators", type=int, default=150)
        parser.add_argument("--test-size", type=float, default=0.2)
        parser.add_argument("--random-state", type=int, default=42)

    def handle(self, *args, **options):
        n_estimators = options["estimators"]
        test_size = options["test_size"]
        random_state = options["random_state"]

        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(self.style.NOTICE("  OPTIMIZED ML Model Training - Dropout Detection"))
        self.stdout.write(self.style.NOTICE("=" * 60))

        # -- 1. Data Collection --
        students = Student.objects.exclude(target="").exclude(target__isnull=True)
        total = students.count()
        if total == 0:
            self.stderr.write(self.style.ERROR("No labeled students found."))
            return

        self.stdout.write(f"\n[1/6] Loading data for {total} students...")
        
        data = []
        target = []
        for s in students.iterator():
            row = {field: getattr(s, field) for field in FEATURE_FIELDS}
            data.append(row)
            target.append(s.target)

        df = pd.DataFrame(data)
        y = np.where(np.array(target) == 'Dropout', 1, 0)

        # -- 2. Stable Encoding --
        self.stdout.write("[2/6] Applying Ordinal Encoding to categorical features...")
        # handle_unknown='use_encoded_value' is key for stability
        encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
        df[CATEGORICAL_FIELDS] = encoder.fit_transform(df[CATEGORICAL_FIELDS].astype(str))
        
        # Ensure all other columns are numeric
        X = df.astype(float).values

        # -- 3. Split & Balance --
        self.stdout.write(f"[3/6] Splitting data (Test size: {test_size})...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        self.stdout.write("[4/6] Applying SMOTE to handle class imbalance...")
        sm = SMOTE(random_state=random_state)
        X_train_res, y_train_res = sm.fit_resample(X_train, y_train)

        # -- 4. Model Training --
        self.stdout.write(f"[5/6] Training Random Forest (Trees: {n_estimators}, Max Depth: 12)...")
        # Reduced max_depth to prevent overfitting (100% confidence issues)
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=12,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1
        )
        
        # Cross-validation on Resampled Training Data
        cv_scores = cross_val_score(model, X_train_res, y_train_res, cv=5)
        self.stdout.write(f"      - CV Mean Accuracy: {cv_scores.mean()*100:.2f}%")
        
        model.fit(X_train_res, y_train_res)

        # -- 5. Evaluation --
        self.stdout.write("[6/6] Finalizing Model Evaluation...")
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred)
        
        self.stdout.write(self.style.SUCCESS(f"\n      >>> Test Accuracy: {acc*100:.2f}%"))
        self.stdout.write(self.style.SUCCESS(f"      >>> Test F1-Score: {f1:.4f}"))
        
        self.stdout.write("\n[ANALYSIS] Confusion Matrix:")
        self.stdout.write(f"      Actual \ Pred | Non-Dropout | Dropout")
        self.stdout.write(f"      --------------|-------------|---------")
        self.stdout.write(f"      Non-Dropout   | {cm[0,0]:11} | {cm[0,1]:7}")
        self.stdout.write(f"      Dropout       | {cm[1,0]:11} | {cm[1,1]:7}")

        self.stdout.write("\n[REPORT] Classification Detail:")
        self.stdout.write(classification_report(y_test, y_pred, target_names=['Non-Dropout', 'Dropout']))

        # -- 6. Save Artifacts --
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(model, os.path.join(MODEL_DIR, "dropout_model.joblib"))
        joblib.dump(encoder, os.path.join(MODEL_DIR, "feature_encoder.joblib"))
        joblib.dump(FEATURE_FIELDS, os.path.join(MODEL_DIR, "feature_names.joblib"))
        
        # Save LabelEncoder for consistency (used by predictor to map labels)
        le = LabelEncoder().fit(['Non-Dropout', 'Dropout'])
        joblib.dump(le, os.path.join(MODEL_DIR, "label_encoder.joblib"))

        importances = {FEATURE_FIELDS[i]: float(model.feature_importances_[i]) for i in range(len(FEATURE_FIELDS))}
        joblib.dump(importances, os.path.join(MODEL_DIR, "feature_importances.joblib"))

        self.stdout.write(self.style.SUCCESS(f"\n[DONE] Model and Encoder saved to {MODEL_DIR}"))
