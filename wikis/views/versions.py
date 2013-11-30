# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.shortcuts import render_to_response
from wikis.models.versions import Version

@login_required
def get_drafts(request):
    """ return all drafts for a the logged in user"""
    list_drafts = Version.objects.filter(version_user=request.user, version_status="2")
    if not list_drafts:
        list_drafts = None

    c = RequestContext(request, {'list_drafts': list_drafts,
                                 })
    return render_to_response('wikis/list_drafts.html', c)
