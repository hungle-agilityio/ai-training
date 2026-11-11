import os
from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from reviews import followup_repository, reply_service
from reviews.models import Branch, Business, ReplyTemplate, Review
from reviews.repositories import create_review
from reviews.template_repository import create_template

DEMO_USERNAME = "demo"
DEMO_PASSWORD_VARIABLE = "REVIEWRADAR_DEMO_PASSWORD"
DAYS_BETWEEN_REVIEWS = 20
MIN_REPLIED_RATING = 4
DEMO_REPLY_TEXT = "Thank you for your kind words. We hope to see you again soon."
DEMO_BAD_REPLY_TEXT = "We are sorry about your visit. Our manager will call you to make it right."
# Reply delay in hours after the review, keyed by (branch, review text).
DEMO_BAD_REPLY_DELAY_HOURS: dict[tuple[str, str], int] = {
    ("Airport", "Front desk understaffed, queue out the door."): 30,
    ("Riverside", "Phone line always busy, could not book."): 3,
    ("Riverside", "Nhân viên lễ tân chưa nhiệt tình"): 20,
}
# Demo follow-up cases as (status, note), keyed by (branch, review text); the rest stay open.
DEMO_FOLLOWUPS: dict[tuple[str, str], tuple[str, str]] = {
    ("Riverside", "Phone line always busy, could not book."): (
        "contacted",
        "Called the customer back and booked a visit for the next morning.",
    ),
    ("Riverside", "Nhân viên lễ tân chưa nhiệt tình"): (
        "resolved",
        "Talked with the front desk team about greeting every customer.",
    ),
}

# Demo goals; a location not listed has no goal.
DEMO_GOALS: dict[str, Decimal] = {"Downtown": Decimal("4.5"), "Riverside": Decimal("3.0")}

# Demo reply templates: (name, kind, text).
DEMO_TEMPLATES: list[tuple[str, str, str]] = [
    (
        "Thank you",
        "good",
        "Thank you for your kind words! The team at {location} is glad you had a good visit, "
        "and we hope to see you again soon.",
    ),
    (
        "We are sorry",
        "bad",
        "We are sorry your visit to {location} did not go well. "
        "Please contact us so we can make it right.",
    ),
    (
        "Thanks for the feedback",
        "any",
        "Thank you for taking the time to share your feedback about {location}. "
        "It helps us improve.",
    ),
]

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
        ReplyTemplate.objects.all().delete()
        for name, kind, text in DEMO_TEMPLATES:
            create_template(name=name, text=text, kind=kind)

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
        branch = Branch.objects.create(
            business=business, name=name, target_score=DEMO_GOALS.get(name)
        )
        for offset, (rating, text) in enumerate(items):
            review = create_review(
                branch=branch,
                rating=rating,
                text=text,
                created_at=now - timedelta(days=offset * DAYS_BETWEEN_REVIEWS),
            )
            case = DEMO_FOLLOWUPS.get((name, text))
            if case is not None:
                status, note = case
                followup_repository.save_followup(
                    review_id=review.id, status=status, note=note, user_id=None, now=now
                )
            if rating >= MIN_REPLIED_RATING:
                reply_service.save_reply(review.id, DEMO_REPLY_TEXT, None, now)
                continue
            delay = DEMO_BAD_REPLY_DELAY_HOURS.get((name, text))
            if delay is not None:
                reply_at = review.created_at + timedelta(hours=delay)
                reply_service.save_reply(review.id, DEMO_BAD_REPLY_TEXT, None, reply_at)
