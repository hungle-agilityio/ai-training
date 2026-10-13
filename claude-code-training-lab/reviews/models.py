from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    """A customer review collected from an external source. Data only."""

    external_id = models.CharField(max_length=255, blank=True, default="")
    source = models.CharField(max_length=50, default="manual")
    author_name = models.CharField(max_length=255, blank=True, default="")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    text = models.TextField()
    language = models.CharField(max_length=10, blank=True, default="")
    posted_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-posted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"],
                condition=~models.Q(external_id=""),
                name="unique_review_per_source_external_id",
            ),
        ]

    def __str__(self) -> str:
        return f"Review({self.rating}★ by {self.author_name or 'anonymous'})"
