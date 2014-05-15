#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from models import Guest
from django.db import transaction, IntegrityError
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
import csv
import logging
import datetime

logger = logging.getLogger(__name__)

def guest2string(guest):
    if guest.timestamp is None:
        return u'({0} {1} no show)'.format(guest.name , str(guest.confirmation_code))
    else:
        return u'({0} {1} {2})'.format(guest.name , str(guest.confirmation_code) , str(guest.timestamp)) 

def getCurrentUserName(request):
    return request.user.username

@login_required
def index(request):
    msg = ''
    if 'msg' in request.flash:
        msg = request.flash['msg']
    guest = None
    if 'guest' in request.flash:
        guest = request.flash['guest']
    has_error = False
    if 'has_error' in request.flash:
        has_error = request.flash['has_error']
    context = {'msg': msg, 'guest': guest, 'has_error': has_error}
    return render(request, 'index.html', context)

@login_required
def search(request):
    confirmation_code = request.POST['confirmation_code']
    logger.info('SEARCH: entry using confirmation code ' + str(confirmation_code) + ' by user ' + getCurrentUserName(request))
    guest = None
    msg = ''
    has_error = False
    try:
        guest = Guest.objects.get(confirmation_code=confirmation_code)
        logger.info('SEARCH: found guest ' + guest2string(guest))
        if guest.timestamp != None:
            msg = u'验证失败 验证码已使用'
            has_error = True
    except Guest.DoesNotExist:
        logger.error('SEARCH: invalid confirmation_code ' + confirmation_code)
        guest = None
        msg = u'验证失败 验证码{0}无效'.format(confirmation_code)
        has_error = True
    request.flash['msg'] = msg
    request.flash['guest'] = guest
    request.flash['has_error'] = has_error
    return HttpResponseRedirect(reverse(index))

@login_required
def checkin(request):
    confirmation_code = request.POST['confirmation_code']
    msg = ''
    has_error = False
    logger.info('CHECKIN: checking in using confirmation code ' + str(confirmation_code) + ' by user ' + getCurrentUserName(request))
    try:
        with transaction.atomic():
            guest = Guest.objects.select_for_update().get(confirmation_code=confirmation_code)
            logger.info('CHECKIN: found guest ' + guest2string(guest))
            if guest.timestamp is None:
                guest.timestamp = datetime.datetime.now()
                guest.save()
                msg = u'验证成功 ' + guest.name + ' ' +  str(confirmation_code) + ' ' +str(guest.timestamp)
                logger.info('CHECKIN: guest checked in ' + guest2string(guest))
            else:
                msg = u'验证失败 验证码已使用 记录:' + guest.name + ' ' +  str(confirmation_code) + ' ' +str(guest.timestamp)
                logger.error('CHECKIN: confirmation used ' + guest2string(guest))
                has_error = True
    except Guest.DoesNotExist:
        msg = u'验证失败 验证码{0}无效'.format(confirmation_code)
        logger.error('CHECKIN: invalid confirmation_code ' + confirmation_code)
        has_error = True
    request.flash['msg'] = msg
    request.flash['has_error'] = has_error
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
    has_error = False
    if 'has_error' in request.flash:
        has_error = request.flash['has_error']
    context = {'msg': msg, 'has_error': has_error}
    return render(request, 'upload_guest_index.html', context)    

@staff_member_required
def upload_guest(request):
    logger.info('UPLOAD_GUEST entry by user ' + getCurrentUserName(request))
    file = request.FILES['guest_list']
    data = [row for row in csv.reader(file)][1:]
    msg = ''
    has_error = False
    try:
        with transaction.atomic():
            Guest.objects.all().delete()
            for row in data:
                if len(row) != 2:
                    logger.error('UPLOAD_GUEST invalide row ' + str(row))
                    has_error = True
                    msg = u'文件格式错误' + str(row)
                elif len(row[1]) != 5 or str(row[1]).isdigit == False:
                    msg = u'验证码格式错误' + str(row[1])
                    logger.error('UPLOAD_GUEST invalid confirmation_code ' + str(row[1]))
                    has_error = True
                else:
                    Guest.objects.create(name=row[0], confirmation_code=row[1], timestamp=None)
                    logger.info('UPLOAD_GUEST row added ' + str(row))
    except IntegrityError:
        msg = u'验证码重复'
        logger.error('UPLOAD_GUEST duplicate confirmation code')
        has_error = True
    if msg == '':
        msg = u'上传成功'
        logger.info('UPLOAD_GUEST success')
    request.flash['msg'] = msg
    request.flash['has_error'] = has_error
    return HttpResponseRedirect(reverse(upload_guest_index))

@staff_member_required
def download_guest(request):
    logger.info('DOWNLOAD_GUEST entry by user ' + getCurrentUserName(request))
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="guest_list.csv"'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Confirmation Code', 'Time'])
    for guest in Guest.objects.all():
        timestamp = ' '
        if guest.timestamp != None:
            timestamp = str(guest.timestamp)
        writer.writerow([guest.name.encode('utf-8'), guest.confirmation_code, str(timestamp)])
    return response    

