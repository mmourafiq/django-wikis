# -*- coding: utf-8 -*-
'''
Created on Mar 20, 2011

@author: Mourad Mourafiq

@copyright: Copyright © 2011

other contributers:
'''
from django import forms
from django.forms import widgets
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from wikis.models.articles import Article


class CommaSeparatedUserInput(widgets.Input):
    input_type = 'text'
    
    def render(self, id, value, attrs=None):
        if value is None:
            value = ''
        elif isinstance(value, (list, tuple)):
            value = (', '.join([str(user.id) for user in value]))
        return super(CommaSeparatedUserInput, self).render(id, value, attrs)
        


class CommaSeparatedUserField(forms.Field):
    widget = CommaSeparatedUserInput
    
    def __init__(self, *args, **kwargs):
        recipient_filter = kwargs.pop('recipient_filter', None)
        self._recipient_filter = recipient_filter
        super(CommaSeparatedUserField, self).__init__(*args, **kwargs)
        
    def clean(self, value):
        super(CommaSeparatedUserField, self).clean(value)
        if not value:
            return ''
        if isinstance(value, (list, tuple)):
            return value
        
        ids = set(value.split(','))
        ids_set = set([str(id) for id in ids if id != ""])
        users = list(User.objects.filter(id__in=ids_set))
        unknown_ids = ids_set ^ set([str(user.id) for user in users])
        
        recipient_filter = self._recipient_filter
        invalid_users = []
        if recipient_filter is not None:
            for r in users:
                if recipient_filter(r) is False:
                    users.remove(r)
                    invalid_users.append(r.id)
        
        if unknown_ids or invalid_users:
            raise forms.ValidationError(_(u"The following id are incorrect: %(users)s") % {'users': ', '.join([str(i) for i in list(unknown_ids | set(invalid_users))])})
        
        return users

class CommaSeparatedArticleInput(widgets.Input):
    input_type = 'text'
    
    def render(self, id, value, attrs=None):
        if value is None:
            value = ''
        elif isinstance(value, (list, tuple)):
            value = (', '.join([str(user.id) for user in value]))
        return super(CommaSeparatedArticleInput, self).render(id, value, attrs)
        


class CommaSeparatedArticleField(forms.Field):
    widget = CommaSeparatedArticleInput
    
    def __init__(self, *args, **kwargs):
        article_filter = kwargs.pop('article_filter', None)
        self._article_filter = article_filter
        super(CommaSeparatedArticleField, self).__init__(*args, **kwargs)
        
    def clean(self, value):
        super(CommaSeparatedArticleField, self).clean(value)
        if not value:
            return ''
        if isinstance(value, (list, tuple)):
            return value
        
        ids = set(value.split(','))
        ids_set = set([str(id) for id in ids if id != ""])
        articles = list(Article.objects.filter(id__in=ids_set))
        unknown_ids = ids_set ^ set([str(article.id) for article in articles])
        
        article_filter = self._article_filter
        invalid_articles = []
        if article_filter is not None:
            for r in articles:
                if article_filter(r) is False:
                    articles.remove(r)
                    invalid_articles.append(r.id)
        
        if unknown_ids or invalid_articles:
            raise forms.ValidationError(_(u"The following id are incorrect: %(articles)s") % {'articles': ', '.join([str(i) for i in list(unknown_ids | set(invalid_articles))])})
        
        return articles