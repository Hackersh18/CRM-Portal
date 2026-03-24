from django.core.management.base import BaseCommand

from main_app.seed_reference import seed_all


class Command(BaseCommand):
    help = (
        "Create default Lead statuses, Activity types, and Next actions (same as a fresh local DB / "
        "migrations 0017 and 0019). Safe to run multiple times; only missing codes are inserted."
    )

    def handle(self, *args, **options):
        counts = seed_all()
        self.stdout.write(
            self.style.SUCCESS(
                "Done. New rows created — "
                f"LeadStatus: {counts['lead_statuses']}, "
                f"ActivityType: {counts['activity_types']}, "
                f"NextAction: {counts['next_actions']}."
            )
        )
        self.stdout.write(
            "Existing rows (same code) were left unchanged. "
            "To copy extra custom rows from another DB, use dumpdata/loaddata for those models."
        )
