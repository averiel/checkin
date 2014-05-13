from django.conf.urls import patterns, url

from checkinAdmin import views

urlpatterns = patterns('',
  url(r'^$', views.index, name='index'),
  url(r'^checkin$', views.checkin, name='checkin'),
  url(r'^logout$', views.logout_view, name='logout'),
  url(r'^upload_guest_index$', views.upload_guest_index, name='upload_guest_index'),
  url(r'^upload_guest$', views.upload_guest, name='upload_guest'),
  url(r'^download_guest$', views.download_guest, name='download_guest'),
)