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

    def __str__(self) -> str:
        return f"{self.branch_id}: {self.rating}"
