# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings
from wikis.settings import *
from permissions.forms import PermissionForm
if 'taggit' in settings.INSTALLED_APPS:
    from taggit import forms as ft
else:
    ft = None

class ArticleForm(PermissionForm):
    title = forms.CharField(label=_('Title'))
    contents = forms.CharField(label=_('Contents'),
                               widget=forms.Textarea(), required=False)
    status = forms.ChoiceField(label=_('Status'),widget=forms.Select(), choices=VERSION_STATUS,
                                           initial="1")
    
    category = forms.ChoiceField(widget=forms.RadioSelect(), choices=WIKI_CATEGORY,
                                     initial="2", label=_('Category'))
    if ft:
        tags = ft.TagField(label=("Tags"), required=False)
    honeypot = forms.CharField(required=False,
                                    label=_('If you enter anything in this field '\
                                            'your comment will be treated as spam'))    
    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        if ft:
            self.fields.keyOrder = ['title', 'contents', 'status','category',
                                'visibility', 'can_read', 'protection', 'can_write', 'tags','honeypot']
        else:
            self.fields.keyOrder = ['title', 'contents', 'status','category',
                                'visibility', 'can_read', 'protection', 'can_write', 'honeypot']
        self.fields['title'].widget.attrs['class'] = 'title'
        self.fields['contents'].widget.attrs['class'] = 'description'
        self.fields['status'].widget.attrs['class'] = 'description'
        
    def clean_honeypot(self):
        """Check that nothing's been entered into the honeypot."""
        value = self.cleaned_data["honeypot"]
        if value:
            raise forms.ValidationError(self.fields["honeypot"].label)
        return value
