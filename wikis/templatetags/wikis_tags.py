# -*- coding: utf-8 -*-
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
