import csv
from django.core.management.base import BaseCommand, CommandError
from accounts.models import Organization
from monitor.models import CostSnapshot


class Command(BaseCommand):
    help = "Loads synthetic_costs.csv into the CostSnapshot table for a specific organization."

    def add_arguments(self, parser):
        parser.add_argument(
            "--org", type=str, required=True,
            help="Name of the organization to load this data into (must already exist)."
        )
        parser.add_argument(
            "--file", type=str, default="synthetic_costs.csv",
            help="Path to the CSV file to load (default: synthetic_costs.csv)"
        )

    def handle(self, *args, **options):
        org_name = options["org"]
        file_path = options["file"]

        try:
            organization = Organization.objects.get(name=org_name)
        except Organization.DoesNotExist:
            raise CommandError(
                f"No organization named '{org_name}' exists. "
                f"Register an account for it first, or check the exact name in /admin/."
            )

        deleted_count, _ = CostSnapshot.objects.filter(organization=organization).delete()
        self.stdout.write(f"Cleared {deleted_count} existing records for {org_name}.")

        with open(file_path, newline="") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                CostSnapshot.objects.create(
                    organization=organization,
                    date=row["date"],
                    service=row["service"],
                    cost_usd=row["cost_usd"],
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Loaded {count} cost records for {org_name}."))