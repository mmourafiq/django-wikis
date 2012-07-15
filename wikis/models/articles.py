# -*- coding: utf-8 -*-
'''
Created on Mar 20, 2011

@author: Mourad Mourafiq

@copyright: Copyright © 2011

other contributers:
'''
import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils.translation import ugettext, ugettext_lazy as _
from wikis.settings import *
from wikis.managers.articles import ActiveManager
from wikis.files import get_attachment_path
from permissions.models import Permission
if 'djangosphinx' in settings.INSTALLED_APPS:
    from djangosphinx.models import SphinxSearch
else:
    SphinxSearch = None
if 'taggit' in settings.INSTALLED_APPS:
    from taggit.managers import TaggableManager
else:
    TaggableManager = None

class ShouldHaveExactlyOneRootSlug(Exception):
    pass


class Article(models.Model):
    """
    Wiki referring to Revision model for actual content.
    'slug' and 'parent' field should be maintained centrally, since users
    aren't allowed to change them, anyways.
    """


    author = models.ForeignKey(User, blank=True, null=True, related_name="created_articles")
    parent = models.ForeignKey('self', verbose_name=_('Parent cal slug'),
                               help_text=_('Affects URL structure and possibly inherits permissions'),
                               null=True, blank=True,default=None)
    related = models.ManyToManyField('self', verbose_name=_('Related cals'), symmetrical=True,
                                     help_text=_('Sets a symmetrical relation other articles'),
                                     blank=True, null=True)

    title = models.CharField(max_length=140, verbose_name=_('Cal title'),
                             blank=False)
    slug = models.SlugField(max_length=140, verbose_name=_('slug'),
                            help_text=_('Letters, numbers, underscore and hyphen.'
                                        ' Do not use reserved words \'create\','
                                        ' \'history\' and \'edit\'.'),
                                                                    blank=True)
    created_at = models.DateTimeField(_('created at'), default=datetime.now)
    modified_on = models.DateTimeField(_('modified on'), default=datetime.now)
    is_active = models.BooleanField(default=True)
    permissions = models.ForeignKey(Permission, verbose_name=_('Permissions'),
                                    blank=True, null=True,
                                    help_text=_('Permission group'))
    locked = models.BooleanField(default=False, verbose_name=_('Locked for editing'))
    locked_by = models.ForeignKey(User, related_name='locked', blank=True, null=True,)
    current_version = models.OneToOneField('Version', related_name='%(app_label)s_%(class)s_version',
                                            blank=True, null=True, editable=True)
    category = models.CharField(max_length=1, choices=WIKI_CATEGORY)
    if TaggableManager:
        tags = TaggableManager()

    # TODO: add link list
    active = ActiveManager()
    objects = models.Manager()
    if SphinxSearch:    
        search_articles = SphinxSearch(
            index='articles articles_delta',
            weights={
                     'title':100,
                     'slug':100,
                     },
            )

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')
        app_label = 'wikis'
        unique_together = (('slug', 'parent'),)

    def __unicode__(self):
        return self.title

    def attachments(self):
        return Attachment.objects.filter(article__exact=self)

    def attachment_profile(self):
        attachments =  Attachment.objects.filter(article__exact=self).order_by('-uploaded_on')
        if attachments.count()>0:
            return attachments[0].thumbnail.url
        else :
            return False

    @classmethod
    def get_cal_parent(cls, path):
        """
        allows to retrieve the first article in the path, to make it
        as the parent for the current event article.
        otherwise we take the root as the default parent.
        """
        if path != []:
            if int(path[-1].cal_type) > 0:
                try:
                    return path[-1].pagecal
                except Article.DoesNotExist:
                    return Article.get_cal_parent(path[:-1])
            else:
                return Article.get_cal_parent(path[:-1])
        else:
            return None

    @classmethod
    def get_root(cls):
        """Return the root article, which should ALWAYS exist..
        except the very first time the Article is loaded, in which
        case the user is prompted to create this article."""
        try:
            return Article.objects.filter(parent__exact=None)[0]
        except:
            raise ShouldHaveExactlyOneRootSlug()

    def get_url(self):
        """Return the cal URL for an article"""
        if self.parent:
            return self.parent.get_url() + '/' + self.slug
        else:
            return self.slug

    @models.permalink
    def get_absolute_url(self):
        url = 'article_view'
        return (url, [self.get_url()])

    @models.permalink
    def get_edit_url(self):
        url = 'article_edit'
        return (url, [self.get_url()])

    @models.permalink
    def get_tree_view_url(self):
        url = 'article_tree'
        return (url, [self.get_url()])

    @models.permalink
    def get_upload_photo_url(self):
        url = 'article_upload_photo'
        return (url, [self.get_url()])

    @models.permalink
    def get_add_related_url(self):
        url = 'article_related'
        return (url, [self.get_url()])

    @models.permalink
    def get_cancel_url(self):
        url = 'article_cancel'
        return (url, [self.get_url()])

    @models.permalink
    def get_reactivate_url(self):
        url = 'article_reactivate'
        return (url, [self.get_url()])

    @models.permalink
    def get_set_parent_url(self):
        url = 'article_parent'
        return (url, [self.get_url()])

    @classmethod
    def get_url_reverse(cls, path, article, return_list=[]):
        """Lookup a URL and return the corresponding set of articles
        in the path."""
        if path == []:
            return return_list + [article]
        # Lookup next child in path
        try:
            a = Article.active.get(parent__exact=article, slug__exact=str(path[0]))
            return cls.get_url_reverse(path[1:], a, return_list + [article])
        except Exception, e:
            return None

    def can_write_l(self, user):
        """Check write permissions and locked status"""
        return not self.locked and self.permissions.can_write_obj(user)

    def can_attach(self, user):
        return self.can_write_l(user)

    def delete(self, user):
        if self.can_write_l(user) and user == self.author:
            self.is_active = False
            self.save()
            return True
        return False

    def reactivate(self, user):
        """reactivate a cal if deleted"""
        if self.can_write_l(user) and user == self.author:
            self.is_active = True
            self.save()
            return True
        return False

    def edit_relatives(self, relatives):
        """ change permissions to users on the current cal """
        old_relatives = []
        relatives_l = self.related.all()
        for i in relatives_l:
            old_relatives.append(i)
        for i in relatives:
            if i in old_relatives:
                old_relatives.remove(i)
            else:
                self.related.add(i)

        for i in old_relatives:
            self.related.remove(i)

    def set_parent(self, parent):
        """ set a parent for the current cal (should be a pagecal) """
        # Ensure doesn't already appended or it's child of the current one or it is itself
        if (parent == self):
            return
        if (parent.parent == self):
            #the child is currently the parent of the future parent
            parent.parent = self.parent
            self.parent = parent
            parent.save()
            self.save()
        elif (self.parent == parent):
            #the child parent is the same future parent nothing to do then
            return
        else :
            #the parent and the child aren't related
            self.parent = parent
            self.save()

DEFAULT_PICTURE = 'cal.gif'

class Attachment(models.Model):
    article = models.ForeignKey(Article, verbose_name=_('Article'))
    picture = models.ImageField(upload_to=get_attachment_path, default=DEFAULT_PICTURE, blank=True, null=True)
    thumbnail = models.ImageField(upload_to='uploads/thumbs/articles/', blank=True, null=True,
         editable=False)
    uploaded_by = models.ForeignKey(User, blank=True, verbose_name=_('Uploaded by'), null=True)
    uploaded_on = models.DateTimeField(default=datetime.now,verbose_name=_('Upload date'))

    class Meta:
        app_label = 'wikis'

    def save(self, force_insert=False, force_update=False):
        #get mtime stats from file
        thumb_update = False

        if self.thumbnail:
            try:
                if self.picture:
                    statinfo1 = os.stat(self.picture.path)
                    statinfo2 = os.stat(self.thumbnail.path)
                    if statinfo1 > statinfo2:
                        thumb_update = True
                else:
                    self.picture = DEFAULT_PICTURE
                    thumb_update = True

            except OSError:
                thumb_update = True

        if self.picture and not self.thumbnail or thumb_update:
            from PIL import Image

            THUMB_SIZE = (200,200)

            #self.thumbnail = self.picture

            image = Image.open(self.picture)

            if image.mode not in ('L', 'RGB'):
                image = image.convert('RGB')

            image.thumbnail(THUMB_SIZE, Image.ANTIALIAS)
            (head, tail) = os.path.split(self.picture.path)
            (a, b) = os.path.split(self.picture.name)

            if not os.path.isdir(head + '/uploads/thumbs/articles'):
                os.mkdir(head + '/uploads/thumbs/articles')

            image.save(head + '/uploads/thumbs/articles/' + tail)

            self.thumbnail = 'uploads/thumbs/articles/' + b

        super(Attachment, self).save()