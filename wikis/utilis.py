# -*- coding: utf-8 -*-
'''
Created on Mar 20, 2011

@author: Mourad Mourafiq

@copyright: Copyright © 2011

other contributers:
'''
from django.shortcuts import get_object_or_404, render_to_response 
from django.template import RequestContext, Context, loader
from django.utils.html import strip_tags
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup, Comment
import re
from wikis.models.articles import Article

def find_key_for_caltype(dic, val):
    """return the key of dictionary dic given the value"""
    return [k for k, v in dic.iteritems() if v == val][0]

def get_url_path(url):
    """Return a list of all actual elements of a url, safely ignoring
    double-slashes (//) """
    return filter(lambda x: x != '', url.split('/'))

def fetch_from_url(request, url):
    """Analyze URL, returning the article and the articles in its path
    If something goes wrong, return an error HTTP response"""

    err = None
    article = None
    path = None
    
    url_path = get_url_path(url)

    try:
        root = Article.get_root()
    except:
        err = not_found(request, '')
        return (article, path, err)

    if url_path and root.slug == url_path[0]:
        url_path = url_path[1:]

    path = Article.get_url_reverse(url_path, root)
    if not path:
        err = not_found(request, '/' + '/'.join(url_path))
    else:
        article = path[-1]
    return (article, path, err)
        
def not_found(request, wiki_url):
    """Generate a NOT FOUND message for some URL"""
    return render_to_response('simplewiki_error.html',
                              RequestContext(request, {'wiki_err_notfound': True,
                                                       'wiki_url': wiki_url}))
    

def check_permissions(request, article, check_read=False, check_write=False, check_locked=False):
    
    read_err = check_read and not article.permissions.can_read_obj(request.user)
    write_err = check_write and not article.permissions.can_write_obj(request.user)
    locked_err = check_locked and article.locked and not request.user == article.locked_by 

    if read_err or write_err or locked_err:
        c = RequestContext(request, {'article': article,
                                     'err_noread': read_err,
                                     'err_nowrite': write_err,
                                     'err_locked': locked_err, })
        # TODO: Make this a little less jarring by just displaying an error
        #       on the current page? 
        return render_to_response('wiki_error.html', c)
    else:
        return None

def get_permissions(request, article):
    wiki_read = article.permissions.can_read_obj(request.user)
    wiki_write = article.permissions.can_write_obj(request.user)
    return wiki_read, wiki_write


def errors_as_json(form, striptags=False):
    error_summary = {}
    errors = {}
    for error in form.errors.iteritems():
        errors.update({error[0] : unicode(strip_tags(error[1]) \
            if striptags else error[1])})
    error_summary.update({'errors' : errors })
    return error_summary

def sanitizeHtml(value, base_url=None):
    rjs = r'[\s]*(&#x.{1,7})?'.join(list('javascript:'))
    rvb = r'[\s]*(&#x.{1,7})?'.join(list('vbscript:'))
    re_scripts = re.compile('(%s)|(%s)' % (rjs, rvb), re.IGNORECASE)
    validTags = 'blockquote div p i strong b u a h1 h2 h3 pre br font ul ol li'.split()
    validAttrs = 'href src width height align color'.split()
    urlAttrs = 'href src'.split() # Attributes which should have a URL
    soup = BeautifulSoup(value)
    for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
        # Get rid of comments
        comment.extract()
    for tag in soup.findAll(True):
        if tag.name not in validTags:
            tag.hidden = True
        attrs = tag.attrs
        tag.attrs = []
        for attr, val in attrs:
            if attr in validAttrs:
                val = re_scripts.sub('', val) # Remove scripts (vbs & js)
                if attr in urlAttrs:
                    val = urljoin(base_url, val) # Calculate the absolute url
                tag.attrs.append((attr, val))

    return soup.renderContents().decode('utf8')