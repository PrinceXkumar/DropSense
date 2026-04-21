"""
Management command to scan all students for high risk and send alerts.

Usage:
    python manage.py scan_risk_alerts
    python manage.py scan_risk_alerts --email admin@example.com
    python manage.py scan_risk_alerts --telegram
"""

from django.core.management.base import BaseCommand

from students.models import Student
from students.risk_engine import calculate_risk
from students.alerts import send_high_risk_email, send_telegram_alert


class Command(BaseCommand):
    help = "Scan all students for high dropout risk and send alerts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            nargs="*",
            help="Email addresses to send alerts to.",
        )
        parser.add_argument(
            "--telegram",
            action="store_true",
            help="Send alerts via Telegram (uses settings.TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show alerts without actually sending them.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit the number of alerts sent (useful for testing). Default is 0 (no limit).",
        )

    def handle(self, *args, **options):
        students = Student.objects.all()
        high_risk = []

        for student in students.iterator():
            risk = calculate_risk(student)
            if risk["risk_level"] == "High":
                high_risk.append((student, risk))

        self.stdout.write(
            self.style.WARNING(
                f"Found {len(high_risk)} high-risk students out of {students.count()} total."
            )
        )

        if options.get("dry_run"):
            for student, risk in high_risk:
                self.stdout.write(
                    f"  ⚠ Student #{student.id} | Score: {risk['risk_score']} | "
                    f"Reasons: {', '.join(risk['reasons'][:3])}"
                )
            self.stdout.write(self.style.NOTICE("Dry run — no alerts sent."))
            return

        sent_email = 0
        sent_telegram = 0

        limit = options.get("limit", 0)
        if limit > 0:
            high_risk = high_risk[:limit]
            self.stdout.write(self.style.NOTICE(f"Limiting alerts to {limit} students for this run..."))

        recipients = options.get("email") or []
        use_telegram = options.get("telegram", False)

        for student, risk in high_risk:
            if recipients:
                send_high_risk_email(student, risk, recipients)
                sent_email += 1
            if use_telegram:
                send_telegram_alert(student, risk)
                sent_telegram += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Alerts sent — Email: {sent_email}, Telegram: {sent_telegram}"
            )
        )
