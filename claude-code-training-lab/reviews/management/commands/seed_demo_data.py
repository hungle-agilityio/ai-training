import os
from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from reviews.models import Branch, Business, Review
from reviews.repositories import create_review

DEMO_USERNAME = "demo"
DEMO_PASSWORD_VARIABLE = "REVIEWRADAR_DEMO_PASSWORD"

DEMO_REVIEWS: dict[str, list[tuple[int, str]]] = {
    "Airport": [
        (2, "Waited 50 minutes, nobody apologized."),
        (2, "Front desk understaffed, queue out the door."),
        (3, "Doctor was great but check-in was slow."),
        (1, "Billing mistake and nobody called back."),
    ],
    "Downtown": [
        (5, "Friendly staff, quick visit."),
        (4, "Clean and efficient."),
        (3, "Parking is expensive."),
        (5, "Đau chân đỡ hẳn, nhân viên thân thiện"),
        (3, "Dau dau khi cho doi"),
    ],
    "Riverside": [
        (4, "Good care, parking is hard."),
        (5, "Best clinic experience I've had."),
        (2, "Phone line always busy, could not book."),
        (4, "Bác sĩ tận tâm, ĐAU LƯNG đã đỡ nhiều"),
        (2, "Nhân viên lễ tân chưa nhiệt tình"),
    ],
}


class Command(BaseCommand):
    help = "Create demo businesses, branches and reviews (deletes existing data first)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--branches", type=int, default=0, help="Extra branches with 3 reviews."
        )
        parser.add_argument(
            "--with-new-branch", action="store_true", help="Add a branch with no reviews."
        )

    def handle(self, *args: Any, **options: Any) -> None:
        Review.objects.all().delete()
        Branch.objects.all().delete()
        Business.objects.all().delete()

        business = Business.objects.create(name="Demo Clinics")
        now = timezone.now()
        for name, items in DEMO_REVIEWS.items():
            self._create_branch(business, name, items, now)
        for index in range(options["branches"]):
            self._create_branch(
                business,
                f"Extra {index + 1}",
                [(4, "ok"), (5, "great"), (3, "fine")],
                now,
            )
        if options["with_new_branch"]:
            Branch.objects.create(business=business, name="Newtown")

        self.stdout.write(self.style.SUCCESS(f"Seeded {Branch.objects.count()} branches."))
        self._set_demo_user()

    def _set_demo_user(self) -> None:
        """The demo account exists only when its password comes from the environment."""
        password = os.environ.get(DEMO_PASSWORD_VARIABLE, "")
        if not password:
            self.stdout.write(f"{DEMO_PASSWORD_VARIABLE} is not set; no demo user.")
            return
        demo, _ = get_user_model().objects.get_or_create(username=DEMO_USERNAME)
        demo.set_password(password)
        demo.save()
        self.stdout.write(f"Demo user: {DEMO_USERNAME}")

    @staticmethod
    def _create_branch(
        business: Business, name: str, items: list[tuple[int, str]], now: Any
    ) -> None:
        branch = Branch.objects.create(business=business, name=name)
        for offset, (rating, text) in enumerate(items):
            create_review(
                branch=branch,
                rating=rating,
                text=text,
                created_at=now - timedelta(days=offset),
            )
