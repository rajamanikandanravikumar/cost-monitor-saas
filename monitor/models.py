from django.db import models
from accounts.models import Organization


class CostSnapshot(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, null=True, blank=True
    )
    date = models.DateField()
    service = models.CharField(max_length=50)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=2)
    is_anomaly = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service} - {self.date} - ${self.cost_usd}"

    class Meta:
        ordering = ['-date']