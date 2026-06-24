from django.db import models
from django.contrib.auth.models import User


class Rock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collection')
    type = models.ForeignKey("Type", on_delete=models.CASCADE, related_name='rocks')
    name = models.CharField(max_length=155)
    weight = models.DecimalField(max_digits=5, decimal_places=2)