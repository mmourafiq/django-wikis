# -*- coding: utf-8 -*-
'''
Created on Mar 20, 2011

@author: Mourad Mourafiq

@copyright: Copyright © 2011

other contributers:
'''
from django.contrib import admin

from models.articles import Article, Attachment
from models.versions import Version

admin.site.register(Article)
admin.site.register(Attachment)
admin.site.register(Version)