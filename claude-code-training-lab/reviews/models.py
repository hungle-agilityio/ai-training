from django.conf import settings
from django.db import models


class Business(models.Model):
    name = models.CharField(max_length=120)

    def __str__(self) -> str:
        return self.name


class Branch(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=120)

    def __str__(self) -> str:
        return self.name


class Review(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField()
    text = models.TextField()
    created_at = models.DateTimeField()
    # Normalised copy of `text` for searching; filled by `repositories.create_review`
    search_text = models.TextField(default="", editable=False)

    def __str__(self) -> str:
        return f"{self.branch_id}: {self.rating}"


class ReviewReply(models.Model):
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name="reply")
    text = models.TextField()
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    def __str__(self) -> str:
        return f"reply to {self.review_id}"
