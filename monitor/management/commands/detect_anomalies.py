import os
from decimal import Decimal
from itertools import groupby

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils.html import strip_tags

from monitor.models import CostSnapshot

DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://127.0.0.1:8000/")


class Command(BaseCommand):
    help = "Flags cost anomalies per organization using a rolling average per service, and emails a styled HTML summary per org."

    def add_arguments(self, parser):
        parser.add_argument("--window", type=int, default=7)
        parser.add_argument("--threshold", type=float, default=1.5)
        parser.add_argument("--min-history", type=int, default=3)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--no-email", action="store_true")

    def handle(self, *args, **options):
        window_days = options["window"]
        threshold = Decimal(str(options["threshold"]))
        min_history = options["min_history"]
        dry_run = options["dry_run"]

        flagged_records, changed_records, total_checked = self._run_detection(
            window_days, threshold, min_history
        )

        if not dry_run and changed_records:
            CostSnapshot.objects.bulk_update(changed_records, ["is_anomaly"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Checked {total_checked} records — flagged {len(flagged_records)} anomalies "
                f"across all organizations."
            )
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run: no changes saved, no email sent."))
            return

        if flagged_records and not options["no_email"]:
            self._send_alerts_per_org(flagged_records)

    def _run_detection(self, window_days, threshold, min_history):
        all_records = CostSnapshot.objects.order_by("organization_id", "service", "date")

        flagged_records = []
        changed_records = []
        total_checked = 0

        for (_, _), group in groupby(
            all_records, key=lambda r: (r.organization_id, r.service)
        ):
            records = list(group)

            for i, record in enumerate(records):
                window = records[max(0, i - window_days): i]

                if len(window) < min_history:
                    is_anomaly = False
                else:
                    window_avg = sum(r.cost_usd for r in window) / len(window)
                    is_anomaly = record.cost_usd > (window_avg * threshold)
                    total_checked += 1
                    if is_anomaly:
                        flagged_records.append(record)

                if record.is_anomaly != is_anomaly:
                    record.is_anomaly = is_anomaly
                    changed_records.append(record)

        return flagged_records, changed_records, total_checked

    def _send_alerts_per_org(self, flagged_records):
        """Groups flagged records by organization and sends one styled HTML
        email per org — each admin only ever sees their own org's data."""
        sender_email = os.getenv("EMAIL_HOST_USER")
        if not sender_email:
            self.stdout.write(self.style.WARNING("EMAIL_HOST_USER not set — skipping email."))
            return

        by_org = {}
        for record in flagged_records:
            by_org.setdefault(record.organization, []).append(record)

        for org, records in by_org.items():
            org_name = org.name if org else "Unassigned"
            html_message = self._build_html_email(org_name, records)
            text_message = strip_tags(html_message)

            subject = f"Cost Monitor: {len(records)} anomalies flagged for {org_name}"

            try:
                send_mail(
                    subject=subject,
                    message=text_message,
                    from_email=sender_email,
                    recipient_list=[sender_email],  # TODO: route to org admins in Phase F
                    html_message=html_message,
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS(f"Alert sent for {org_name}."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to send email for {org_name}: {e}"))

    def _build_html_email(self, org_name, records):
        table_rows = ""
        for r in records:
            table_rows += f"""
            <tr style="border-bottom: 1px solid #1e2740;">
                <td style="padding: 12px; color: #cbd5e0;">{r.date}</td>
                <td style="padding: 12px; color: #cbd5e0; font-weight: bold;">{r.service}</td>
                <td style="padding: 12px; color: #f5a623; text-align: right; font-weight: bold;">${r.cost_usd:.2f}</td>
            </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0a0e1a; margin: 0; padding: 20px; color: #e7ebf5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #10162a; border-radius: 8px; border: 1px solid #1e2740; overflow: hidden;">

                <div style="background-color: #10162a; padding: 24px; text-align: center; border-bottom: 1px solid #1e2740;">
                    <h1 style="margin: 0; color: #ffffff; font-size: 20px; letter-spacing: 0.5px;">Cost Monitor</h1>
                    <p style="margin: 6px 0 0 0; color: #35d0e0; font-size: 13px; font-family: monospace;">// anomaly alert for {org_name}</p>
                </div>

                <div style="padding: 24px;">
                    <p style="font-size: 15px; line-height: 1.5; color: #a0aec0;">
                        The daily cost check flagged <span style="color: #f5a623; font-weight: bold;">{len(records)} anomal{"y" if len(records) == 1 else "ies"}</span>
                        for {org_name} — each of these exceeded the recent baseline for that service.
                    </p>

                    <table style="width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 14px;">
                        <thead>
                            <tr style="background-color: #1e2740; text-align: left;">
                                <th style="padding: 12px; color: #6b7797;">Date</th>
                                <th style="padding: 12px; color: #6b7797;">Service</th>
                                <th style="padding: 12px; color: #6b7797; text-align: right;">Cost</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>

                    <div style="text-align: center; margin-top: 32px;">
                        <a href="{DASHBOARD_URL}" style="background-color: #35d0e0; color: #0a0e1a; padding: 12px 28px; text-decoration: none; font-weight: bold; border-radius: 6px; display: inline-block;">
                            View dashboard
                        </a>
                    </div>
                </div>

                <div style="background-color: #0a0e1a; padding: 14px; text-align: center; font-size: 12px; color: #6b7797; border-top: 1px solid #1e2740;">
                    Automated daily check — Cost Monitor
                </div>
            </div>
        </body>
        </html>
        """