from django.contrib import admin
from checkinAdmin.models import Guest
from checkinAdmin.models import GuestCheckInEvent
# Register your models here.
admin.site.register(Guest)
admin.site.register(GuestCheckInEvent)
