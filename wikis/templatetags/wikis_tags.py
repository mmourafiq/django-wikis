# -*- coding: utf-8 -*-
'''
Created on Mar 20, 2011

@author: Mourad Mourafiq

@license: closed application, My_licence, http://www.binpress.com/license/view/l/6f5700aefd2f24dd0a21d509ebd8cdf8

@copyright: Copyright © 2011

other contributers:
'''
import datetime
from django.conf import settings
from django import template
from django.core.urlresolvers import reverse
from django.utils.dateformat import format
import datetime
from django.utils.translation import ugettext_lazy as _

register = template.Library()

@register.inclusion_tag("wikis/_tree.html", takes_context=True)
def draw_tree(context, article):
    context.update({
        'wiki_article': article
    })
    return context