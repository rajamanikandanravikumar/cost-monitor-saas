from django.db import models

# Create your models here.
from django.db import models

class CostSnapshot(models.Model):
    date = models.DateField()
    service = models.CharField(max_length=50)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=2)
    is_anomaly = models.BooleanField(default=False)  # set by our detection logic later, not the CSV
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service} - {self.date} - ${self.cost_usd}"

    class Meta:
        ordering = ['-date']