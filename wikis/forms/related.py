# -*- coding: utf-8 -*-
'''
Created on Mar 20, 2011

@author: Mourad Mourafiq

@copyright: Copyright © 2011

other contributers:
'''
from django.utils.translation import ugettext, ugettext_lazy as _
from django import forms
from wikis.fields import CommaSeparatedArticleField

class RelativeForm(forms.Form):
    relatives = CommaSeparatedArticleField(label=_(u"relatives"), required=False)
    error_css_class = "error"
    def clean_assign(self):
        """
        Check that has assigned the cal to a friend
        """
        if self.cleaned_data['relatives']:
            return self.cleaned_data['relatives']  