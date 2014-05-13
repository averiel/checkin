#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from models import Guest, GuestCheckInEvent
from django.db import transaction, IntegrityError
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
import csv
import logging
import datetime

logger = logging.getLogger(__name__)

def getTimestamp(timestamp):
    datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

@login_required
def index(request):
    msg = ''
    if 'msg' in request.flash:
        msg = request.flash['msg']
    context = {'msg' : msg}
    return render(request, 'index.html', context)

@login_required
def checkin(request):
    confirmationCode = request.POST['confirmation_code']
    logger.info('CHECKIN: checking in using confirmation code ' + str(confirmationCode))
    guests = Guest.objects.filter(confirmation_code=confirmationCode)
    msg = ''
    if len(guests) == 0:
        msg = u'验证失败 验证码{0}无效'.format(confirmationCode)
        logger.error('CHECKIN: invalid code ' + str(confirmationCode))
    else:
        try:
            with transaction.atomic():
                guest_id = guests[0].id
                checkedInGuests = GuestCheckInEvent.objects.filter(guest_id=guest_id)
                if len(checkedInGuests) > 0:
                    msg = (u'验证失败 验证码{0}已被 '.format(confirmationCode) + 
                        checkedInGuests[0].guest.name + u' 于 ' + 
                        str(checkedInGuests[0].timestamp) + u'使用')
                    logger.error('CHECKIN: code has been used ' + str(confirmationCode))
                else:
                    GuestCheckInEvent.objects.create(guest_id=guest_id)
                    msg = u'验证成功 姓名: {0}'.format(guests[0].name)
                    logger.info('CHECKIN: guest ' + msg + ' with code ' + str(confirmationCode) + " is checked in")
        except IntegrityError:
            logger.error('internal error')
            msg = u'请重试'
    request.flash['msg'] = msg
    return HttpResponseRedirect(reverse(index))

@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse(index))

@staff_member_required
def upload_guest_index(request):
    msg = ''
    if 'msg' in request.flash:
        msg = request.flash['msg']
    context = {'msg' : msg}
    return render(request, 'upload_guest_index.html', context)

@staff_member_required
def upload_guest(request):
    logger.info('UPLOAD_GUEST entry')
    file = request.FILES['guest_list']
    data = [row for row in csv.reader(file)][1:]
    msg = ''
    try:
        with transaction.atomic():
            GuestCheckInEvent.objects.all().delete()
            Guest.objects.all().delete()
            for row in data:
                if len(row) != 2:
                    logger.error('UPLOAD_GUEST invalide row ' + str(row))
                    msg = u'文件格式错误'
                else:
                    Guest.objects.create(name=row[0], confirmation_code=row[1])
                    logger.info('UPLOAD_GUEST row added ' + str(row))
    except IntegrityError:
        msg = u'验证码重复'
        logger.error('UPLOAD_GUEST duplicate confirmation code')
    if msg == '':
        msg = u'上传成功'
        logger.info('UPLOAD_GUEST success')
    request.flash['msg'] = msg
    return HttpResponseRedirect(reverse(upload_guest_index))

@staff_member_required
def download_guest(request):
    logger.info('DOWNLOAD_GUEST entry')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="guest_list.csv"'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Attended', 'Time'])
    query = ('select * ' + \
            'from checkinAdmin_guest ' + \
            'left outer join checkinAdmin_guestCheckInEvent on checkinAdmin_guest.id = checkinAdmin_guestCheckInEvent.guest_id')
    for guestData in Guest.objects.raw(query):
        name = guestData.name.encode('utf-8')
        timestamp = guestData.timestamp
        attended = 'yes'
        checkedInTimestamp = ''
        if timestamp is None:
            attended = 'no'
        else:
            checkedInTimestamp = str(timestamp)
        writer.writerow([name, attended, checkedInTimestamp])
    return response    
