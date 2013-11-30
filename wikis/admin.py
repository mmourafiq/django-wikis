# -*- coding: utf-8 -*-
from django.contrib import admin

from models.articles import Article, Attachment
from models.versions import Version

admin.site.register(Article)
admin.site.register(Attachment)
admin.site.register(Version)
