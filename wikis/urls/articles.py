# -*- coding: utf-8 -*-
'''
Created on Mar 20, 2011

@author: Mourad Mourafiq

@copyright: Copyright © 2011

other contributers:
'''
from django.conf.urls import patterns, include, url
from wikis.views import articles as articles

urlpatterns = patterns('',
    url(r'^_create/$', articles.create,
        {'template_name':'wikis/wiki_form.html',
         'next':'article_view','action':'article_create'},
        name='article_create'),
    url(r'^([a-zA-Z\d/_-]*)/_edit/$', articles.edit ,
        {'template_name':'wikis/wiki_form.html', 'next':'article_view'},
        name='article_edit'),
    url(r'^([a-zA-Z\d/_-]*)/_cancel/$', articles.cancel,
        {'next':'article_view'},
        name='article_cancel'),
    url(r'^([a-zA-Z\d/_-]*)/_reactivate/$', articles.reactivate,
        {'next':'article_view'},
        name='article_reactivate'),
    url(r'^([a-zA-Z\d/_-]*)/_add_related/$', articles.add_related,
        {'template_name':'wikis/wiki_form.html', 'next':'article_view'},
        name='article_related'),
    url(r'^([a-zA-Z\d/_-]*)/_set_parent/$', articles.set_parent,
        {'template_name':'wikis/wiki_form.html', 'next':'article_view'},
        name='article_parent'),
    url(r'^([a-zA-Z\d/_-]*)/_add_photo/$', articles.add_attachment,
        {'template_name':'wikis/wiki_form.html', 'next':'article_view'},
        name='article_upload_photo'),
    url(r'^([a-zA-Z\d/_-]*)/_tree/$', articles.tree_view,
        {'template_name':'wikis/tree.html'},
        name='article_tree'),                       
    url(r'^([a-zA-Z\d/_-]*)$', articles.view,
        {'template_name':'wikis/wiki_view.html'},
        name='article_view'),
    url(r'^articles_titles/$', articles.articles_titles, name='articles_titles'),                       
    )
