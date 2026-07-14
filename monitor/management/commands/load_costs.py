import csv
from django.core.management.base import BaseCommand
from monitor.models import CostSnapshot

class Command(BaseCommand):
    help = "Loads synthetic_costs.csv into the CostSnapshot table"

    def handle(self, *args, **kwargs):
        deleted_count, _ = CostSnapshot.objects.all().delete()
        self.stdout.write(f"Cleared {deleted_count} existing records.")

        with open("synthetic_costs.csv", newline="") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                CostSnapshot.objects.create(
                    date=row["date"],
                    service=row["service"],
                    cost_usd=row["cost_usd"],
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Loaded {count} cost records."))