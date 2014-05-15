from django.db import models

class Guest(models.Model):
    name = models.CharField(max_length=100)
    confirmation_code = models.CharField(max_length=5, unique=True)
    timestamp = models.DateTimeField(null=True, blank=True)

