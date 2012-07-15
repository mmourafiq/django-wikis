# -*- coding: utf-8 -*-
'''
Created on Mar 20, 2011

@author: Mourad Mourafiq

@license: closed application, My_licence, http://www.binpress.com/license/view/l/6f5700aefd2f24dd0a21d509ebd8cdf8

@copyright: Copyright © 2011

other contributers:
'''
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from wcals.models.cals import *
from django.db.models import Q
from timelines.models import PublicTimeLine, RelationTimeLine
import datetime

def all_cals(user=None, is_active=None, plannable=None, by_date="C",timeline=None, user_request=None):    
    
    if by_date == "C" or by_date == "M":
        model = BaseCal
    elif by_date == "S" :
        model = EventCal
        
    if is_active is not None:
        baseCals = model.objects.filter(is_active=is_active)
    else :
        baseCals = model.active.all()
    if timeline == "public":
        values = PublicTimeLine.objects.all().values_list('basecal', flat=True)
        baseCals = baseCals.filter(pk__in=list(values))
    elif timeline == "relation":
        values = RelationTimeLine.objects.filter(user=user_request).values_list('basecal', flat=True)
        baseCals = baseCals.filter(pk__in=list(values))
    elif timeline == "public_relation":
        values = list(PublicTimeLine.objects.all().values_list('basecal', flat=True))
        values_relation = list(RelationTimeLine.objects.filter(Q(user=user_request), ~Q(pk__in=list(values))).values_list('basecal', flat=True))
        values.extend(values_relation)
        baseCals = baseCals.filter(pk__in=values)
    if plannable is not None:
        baseCals = baseCals.filter(plannable=plannable)
        
    if user is None:
        return baseCals
    
    user = get_object_or_404(User, pk=user)
    return baseCals.filter(author=user)

def all_calendar_cals(user, is_active=None, plannable=None, timeline=None, user_request=None):    
    user = get_object_or_404(User, pk=user)
    if is_active is not None:
        eventCals = EventCal.objects.filter(is_active=is_active, calendar__user=user)
    else:
        eventCals = EventCal.active.filter(calendar__user=user)
    
    if plannable is not None:
        eventCals = eventCals.filter(plannable=plannable)
    return eventCals
def all_cals_by_params(user=None, cal_type=None, cal_priority=None,
                       is_active=None, cal_category=None,timeline=None,user_request=None,
                       cal_place=None, plannable=None, is_proposition=None,calendar=None, by_date="C"):
    """
    returns all clas by filtering on cal_category
    """
    if calendar is not None and calendar:
        list_cals = all_calendar_cals(user, is_active, plannable, timeline=timeline, user_request=user_request)
    else:
        list_cals = all_cals(user, is_active, plannable, by_date=by_date, timeline=timeline, user_request=user_request)
    if cal_priority is not None:    
        list_cals = list_cals.filter(cal_periority=cal_priority)
    if cal_category is not None:
        list_cals = list_cals.filter(cal_category=cal_category)
    if cal_place is not None:
        list_cals = list_cals.filter(cal_place=cal_place)
    if cal_type is not None:
        list_cals = list_cals.filter(cal_type=cal_type)
    else:
        list_cals = list_cals.filter(cal_type__gt=0)
    if by_date == "S":
        list_cals = list_cals.order_by('-start')
    if (is_proposition is not None):
        if by_date == "C" or by_date == "M":
            list_cals = list_cals.filter(pagecal__eventcal__is_proposition=is_proposition)
        elif by_date == "S":
            list_cals = list_cals.filter(is_proposition=is_proposition)
    return list_cals

def on_this_day(user=None, cal_type=None, in_datetime=None, within=None,
                    cal_priority=None, cal_category=None, cal_place=None,
                    is_active=None, plannable=None, is_proposition=None,user_request=None,
                    timeline=None,since=None, calendar=None, by_date="S"):
    """
    Get all events happening on this day (by default it return non plannable events(wikicals))
    """       
    if in_datetime is None:
        in_datetime = datetime.date.today()   
    
    list_cals = all_cals_by_params(user=user, cal_type=cal_type, timeline=timeline,user_request=user_request,
                                   cal_priority=cal_priority, is_active=is_active,
                                   cal_category=cal_category, cal_place=cal_place,
                                   plannable=plannable, is_proposition=is_proposition,
                                   calendar=calendar,by_date=by_date)
    if within is not None:
        last_datetime = in_datetime + datetime.timedelta(days=int(within))
        return list_cals.order_by('-start').filter(start__gte=in_datetime, start__lte=last_datetime)
    else : 
        return list_cals.order_by('-start').filter(start__startswith=in_datetime)
    

def get_recent_cals(user=None, cal_type=None, in_datetime=None,
                    cal_priority=None, cal_category=None, cal_place=None,
                    is_active=None, plannable=None, is_proposition=None,user_request=None,
                    timeline=None,since=None, calendar=None,by_date='C'):
    """
    This shortcut function allows you to get events that have created
    recently.

    amount is the amount of events you want in the queryset. The default is
    5.

    in_datetime is the datetime you want to check against.  It defaults to
    datetime.datetime.now
    """
    in_datetime = datetime.datetime.now()
    
    list_cals = all_cals_by_params(user=user, cal_type=cal_type, timeline=timeline,user_request=user_request,
                                   cal_priority=cal_priority, is_active=is_active,
                                   cal_category=cal_category, cal_place=cal_place,
                                   plannable=plannable, is_proposition=is_proposition,
                                   calendar=calendar,by_date=by_date)
    if by_date == 'C':
        if since is not None:
            sincae = datetime.datetime.fromtimestamp(int(since))
            return list_cals.order_by('-created_at').filter(created_at__lte=in_datetime, created_at__gte=sincae)
        return list_cals.order_by('-created_at').filter(created_at__lte=in_datetime)
    elif by_date == 'M':
        return list_cals.order_by('-modified_on').filter(modified_on__lt=in_datetime)
    elif by_date == 'S':        
        return list_cals.order_by('-start').filter(end__gte=in_datetime)

def occurrences_after(user=None, cal_type=None, date=None):
    """get a list of all occurrences for events after the date"""
    list_cals = all_cals(user=user, is_active=True, plannable=True)
    return EventListManager(list_cals).occurrences_after(date)

def most_cald(cal_type=None):
    """return a list of most cal'd cals ever"""
    values = PublicTimeLine.objects.all().values_list('basecal', flat=True)
    if cal_type is None:
        return  EventCal.active.filter(pk__in=list(values)).annotate(num_recals=Count('recals')).order_by('-num_recals')
    return EventCal.active.filter(cal_type=cal_type,pk__in=list(values)).annotate(num_recals=Count('recals')).order_by('-num_recals')

def best_cals(cal_type=None):
    """get the best cals ever"""    
