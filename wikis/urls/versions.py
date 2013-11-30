# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from wikis.views import versions as versions
from wikis.views import articles as articles

urlpatterns = patterns('',
    url('^_all/$', versions.get_drafts, name='all_drafts'),
    url('^_lock/(?P<carticle_id>\d+)$', articles.lock_version, name='lock_version'),
    url('^_unlock/(?P<articles_id>\d+)$', articles.unlock_version, name='unlock_version'),
    )
