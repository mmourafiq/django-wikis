# -*- coding: utf-8 -*-
'''
Created on Mar 20, 2011

@author: Mourad Mourafiq

@copyright: Copyright © 2011

other contributers:
'''
import difflib
from django.utils.translation import ugettext, ugettext_lazy as _
from django.db import models
from django.contrib.admin.models import User
from django.db.models import signals
from utils_model.models import sanitizeHtml
from wikis.settings import *
from wikis.models.articles import Article

class Version(models.Model):

    article = models.ForeignKey(Article, verbose_name=_('Article'))
    version_text = models.CharField(max_length=255, blank=True, null=True,
                                     verbose_name=_('Description of change'))
    user = models.ForeignKey(User, verbose_name=_('Modified by'),
                                      blank=False, null=False, related_name='article_revision_user')
    date = models.DateTimeField(auto_now_add=True, verbose_name=_('version date'))
    status = models.CharField(max_length=1, choices=VERSION_STATUS, default="1")
    contents = models.TextField(verbose_name=_('Contents (html formt)'))
    contents_parsed = models.TextField(editable=False, blank=True, null=True)
    counter = models.IntegerField(verbose_name=_('Version#'), default=1, editable=False)
    previous = models.ForeignKey('self', blank=True, null=True, editable=False)

    class Meta:
        verbose_name = _('article revision')
        verbose_name_plural = _('article revisions')
        app_label = 'wikis'

    def __unicode__(self):
        return "r%d" % self.counter

    def get_user(self):
        return self.version_user

    def save(self, **kwargs):
        if self.status == "1":
            # Check if contents have changed... if not, silently ignore save
            if self.article and self.article.current_version:
                if self.article.current_version.contents == self.contents:
                    return
                else:
                    import datetime
                    self.article.modified_on = datetime.datetime.now()
                    self.article.save()

            # Increment counter according to previous revision
            previous = Version.objects.filter(article=self.article).order_by('-counter')
            if previous.count() > 0:
                if previous.count() > previous[0].counter:
                    self.counter = previous.count() + 1
                else:
                    self.counter = previous[0].counter + 1
            else:
                self.counter = 1
            self.previous = self.article.current_version

            #Create pre-parsed contents - no need to parse on-the-fly
#            ext = CAL_MARKDOWN_EXTENSIONS
#            ext += ["wikilinks(base_url=%s/)" % reverse('eventcal_view', args=('',))]
#            self.contents_parsed = markdown(self.contents,
#                                            extensions=ext,
#                                            safe_mode='escape',)
            self.contents_parsed = sanitizeHtml(self.contents)
            super(Version, self).save(**kwargs)
        else:
            if self.article and self.article.current_version:
                if self.article.current_version.contents == self.contents:
                    return
                else:
                    import datetime
                    self.article.modified_on = datetime.datetime.now()
                    self.article.save()
            self.previous = self.article.current_version

            # Create pre-parsed contents - no need to parse on-the-fly
#            ext = CAL_MARKDOWN_EXTENSIONS
#            ext += ["wikilinks(base_url=%s/)" % reverse('cal_view', args=('',))]
#            self.contents_parsed = markdown(self.contents,
#                                            extensions=ext,
#                                            safe_mode='escape',)
            self.contents_parsed = sanitizeHtml(self.contents)
            super(Version, self).save(**kwargs)

    def delete(self, **kwargs):
        """If a current revision is deleted, then regress to the previous
        revision or insert a stub, if no other revisions are available"""
        article = self.article
        if article.current_version == self:
            prev_version = Version.objects.filter(article__exact=article,
                                                    pk__not=self.pk).order_by('-counter')
            if prev_version:
                article.current_revision = prev_version[0]
                article.save()
            else:
                r = Version(article=article,
                             user=article.created_by)
                r.contents = unicode(_('Auto-generated stub'))
                r.version_text = unicode(_('Auto-generated stub'))
                r.save()
                article.current_revision = r
                article.save()
        super(Version, self).delete(**kwargs)

    def get_diff(self):
        if self.previous_version:
            previous = self.previous_version.contents.splitlines(1)
        else:
            previous = []

        # Todo: difflib.HtmlDiff would look pretty for our history pages!
        diff = difflib.unified_diff(previous, self.contents.splitlines(1))
        # let's skip the preamble
        diff.next(); diff.next(); diff.next()

        for d in diff:
            yield d


def set_version(sender, *args, **kwargs):
    """Signal handler to ensure that a new revision is always chosen as the
    current revision - automatically. It simplifies stuff greatly. Also
    stores previous revision for diff-purposes"""
    instance = kwargs['instance']
    created = kwargs['created']
    if created and instance.article and instance.status == "1":
        instance.article.current_version = instance
        instance.article.save()

signals.post_save.connect(set_version, Version)
