from django.db import models

class Guest(models.Model):
    name = models.CharField(max_length=10)
    confirmation_code = models.CharField(max_length=5, unique=True)

class GuestCheckInEvent(models.Model):
    guest = models.OneToOneField(Guest)
    timestamp = models.DateTimeField(auto_now_add=True)

