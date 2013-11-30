# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, Context, loader
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.views.decorators.csrf import csrf_exempt, requires_csrf_token
from django.utils import simplejson
from permissions.models import Permission
from wikis.utilis import fetch_from_url, get_permissions, check_permissions, errors_as_json
from wikis.models.versions import Version
from wikis.models.articles import Article, Attachment
from wikis.forms.articles import ArticleForm
from wikis.forms.parent import ParentForm
from wikis.forms.related import RelativeForm
from wikis.forms.attachment import AttachmentForm
if 'notification' in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None
if 'taggit' in settings.INSTALLED_APPS:
    from taggit.managers import TaggableManager
else:
    TaggableManager = None

@login_required
def create(request, template_name=None, next=None, action=None):
    """this method is used to create a page about something"""
    request_user = request.user
    if request.method == 'POST':
        f = ArticleForm(request.POST)
        if f.is_valid():
            title = f.cleaned_data['title']
            slug = slugify(title)
            category = f.cleaned_data['category']
            protection = f.cleaned_data['protection']
            visibility = f.cleaned_data['visibility']
            can_write = f.cleaned_data['can_write']
            can_read = f.cleaned_data['can_read']
            if Article.objects.filter(slug=slug).count() > 0:
                slug = slug + str(Article.objects.filter(slug__contains=slug).count())
            article = Article(author=request.user, slug=slug, title=title,category=category)

            #Check every thing related to permissions cal_protection and cal_visibility
            if article.permissions is None:
                    permissions = Permission(permission_name='%s_perms' % slug,
                                             visibility=visibility,
                                             protection=protection)
                    permissions.save()
                    article.permissions = permissions
                    article.permissions.can_write.add(request.user)
                    article.permissions.can_read.add(request.user)
            #@todo change "2" to CUSTOM
            if protection == "2":
                for user in can_write:
                        article.permissions.can_write.add(user)
            if visibility == "2":
                for user in can_read:
                        article.permissions.can_read.add(user)


            article.parent = Article.get_root()
            article.save()
            
            if TaggableManager:
                #tagging the article
                tags = f.cleaned_data['tags']
                if tags:
                    article.tags.set(*tags)
            #adding the article description only if the user has checked the add_description
            if not f.cleaned_data['contents'] == '':
                status = f.cleaned_data['status']
                contents = f.cleaned_data['contents']
                new_revision = Version(user=request.user, article=article, status=status,
                                      contents=contents)
                new_revision.save()
            #set the notification object
            #ToNotify(user=request_user, Article=article).save()
            if not request.is_ajax():
                if next == 'wall_home':
                    return HttpResponseRedirect(reverse(next))
                return HttpResponseRedirect(reverse(next, args=(article.get_url(),)))
            response = {'success':True}
        else:
            response = errors_as_json(f)
        if request.is_ajax():
            json = simplejson.dumps(response, ensure_ascii=False)
            return HttpResponse(json, mimetype="application/json")
    else:
        f = ArticleForm()

    c = RequestContext(request, {'wiki_form': f,
                                 'action':reverse(action),
                                 'wiki_edit_protection':False,
                                 'wiki_write': False,
                                 'wiki_read': False,
                                 })

    return render_to_response(template_name, c)

@login_required
def edit(request, wiki_url, template_name=None, next=None):
    """this view is used to edit a page"""
    (article, path, err) = fetch_from_url(request, wiki_url)
    if err:
        return err
    request_user = request.user
    # Check write permissions
    perm_err = check_permissions(request, article, check_write=True, check_locked=True)
    if perm_err:
        return perm_err

    if request.method == 'POST':
        f = ArticleForm(request.POST)
        if f.is_valid():
            article.cal_category = f.cleaned_data['category']
            article.permissions.protection = f.cleaned_data['protection']
            article.permissions.visibility = f.cleaned_data['visibility']
            can_write = f.cleaned_data['can_write']
            can_read = f.cleaned_data['can_read']
            title = f.cleaned_data['title']
            article.title = title
            slug = slugify(title)
            if Article.objects.filter(slug=slug).count() > 0:
                slug = slug + str(Article.objects.filter(slug__contains=slug).count())
            article.slug = slug
            #Check every thing related to permissions cal_protection and cal_visibility
            if f.cleaned_data['protection'] == "2":
                article.permissions.edit_can_write_obj(can_write)
                article.permissions.can_write.add(article.author)
            if f.cleaned_data['visibility'] == "2":
                article.permissions.edit_can_read_obj(can_read)
                article.permissions.can_read.add(article.author)

            article.permissions.save()
            #adding the place only if the user has checked the add_place
            #if f.cleaned['add_place']:

            article.save()
            #adding the article description only if the user has checked the add_description
            if not f.cleaned_data['contents'] == '':
                status = f.cleaned_data['status']
                contents = f.cleaned_data['contents']
                new_revision = Version(user=request.user, article=article, status=status,
                                      contents=contents)                                            
                # Check that something has actually been changed...
                if new_revision.get_diff():
                    new_revision.save()
            if TaggableManager:
                tags = f.cleaned_data['tags']
                if tags:
                    article.tags.set(*tags)
                else:
                    article.tags.clear()
            #notify all concerned users by the object by the new comment
            #users_tonotify = ToNotify.objects.filter(article=article).exclude(user=request_user)
            #for user_tonotify in users_tonotify:
                #user = user_tonotify.user
                #notification.send([user], "article_updated", {'article': article, 'user':request_user,})
            if not request.is_ajax():
                return HttpResponseRedirect(reverse(next, args=(article.get_url(),)))
            response = ({'success':'True'})
        else:
            response = errors_as_json(f)
        if request.is_ajax():
            json = simplejson.dumps(response, ensure_ascii=False)
            return HttpResponse(json, mimetype="application/json")
    else:
        can_read_name = ''
        can_read_id = ''
        for user in article.permissions.can_read.all():
            if not user == request_user:
                can_read_name = can_read_name + user.first_name+' '+user.last_name + ','
                can_read_id = can_read_id + str(user.id) + ','

        can_write_name = ''
        can_write_id = ''
        for user in article.permissions.can_write.all():
            if not user == request_user:
                can_write_name = can_write_name + user.first_name+' '+user.last_name + ','
                can_write_id = can_write_id + str(user.id) + ','
        
        if TaggableManager:
            tags = ''
            for tag in article.tags.all():
                tags = tags + tag.name + ','
            f = ArticleForm({
                  'title': article.title,
                  'contents': article.current_version.contents,
                  'category': article.category,
                  'protection':article.permissions.protection,
                  'visibility': article.permissions.visibility,
                  'can_read': can_read_id,
                  'can_write': can_write_id,
                  'tags' : tags
                  })
        else:
            f = ArticleForm({
                  'title': article.title,
                  'contents': article.current_version.contents,
                  'category': article.category,
                  'protection':article.permissions.protection,
                  'visibility': article.permissions.visibility,
                  'can_read': can_read_id,
                  'can_write': can_write_id,                  
                  })


    c = RequestContext(request, {'wiki_form': f,
                                 'wiki_write': True,
                                 'wiki_read': True,
                                 'wiki_article': article,
                                 'lock': True,
                                 'lock_url': reverse('lock_version', args=[article.id]),
                                 'unlock_url': reverse('unlock_version', args=[article.id]),
                                 'can_read_name': can_read_name,
                                 'can_write_name': can_write_name,
                                 'wiki_attachments_write': article.can_attach(request.user),
                                 'contents': article.current_version.contents,
                                 'title': article.title,
                                 })

    return render_to_response(template_name, c)

def view(request, wiki_url, template_name=None):
    """ view a pagecal """
    (article, path, err) = fetch_from_url(request, wiki_url)
    if err:
        return err
    perm_err = check_permissions(request, article, check_read=True)
    if perm_err:
        return perm_err
    wiki_read, wiki_write = get_permissions(request, article)
    c = RequestContext(request, {'wiki_article': article,
                                 'wiki_read': wiki_read,
                                 'wiki_write': wiki_write,
                                 })
    return render_to_response(template_name, c)

@login_required
def lock_version(request, article_id):
    article = Article.objects.get(pk=article_id)
    if not article.locked :
        article.locked = True
        article.locked_by = request.user
        article.save()
    json_cals = simplejson.dumps({'success':True}, ensure_ascii=False)
    return HttpResponse(json_cals, content_type='application/javascript; charset=utf-8')

@login_required
def unlock_version(request, article_id):
    article = Article.objects.get(pk=article_id)
    if article.locked_by == request.user and article.locked:
        article.locked = False
        article.save()
    json_cals = simplejson.dumps({'success':True}, ensure_ascii=False)
    return HttpResponse(json_cals, content_type='application/javascript; charset=utf-8')

@csrf_exempt
@requires_csrf_token
@login_required
def cancel(request, wiki_url, next=None):
    """ Cancel a article """
    (article, path, err) = fetch_from_url(request, wiki_url)
    if err:
        return err
    request_user = request.user
    # Check write permissions
    perm_err = check_permissions(request, article, check_write=True, check_locked=True)
    if perm_err:
        return perm_err
    if article.delete(request_user):
        """notify all concerned users by the object by the new comment"""
        #users_tonotify = ToNotify.objects.filter(article=article).exclude(user=request_user)
        #for user_tonotify in users_tonotify:
            #user = user_tonotify.user
            #notification.send([user], "article_cancelled", {'article': article, 'user':request_user,})
    if request.is_ajax():
        json_response = simplejson.dumps({
                'success': True,})
        return HttpResponse(json_response, mimetype="application/json")
    return HttpResponseRedirect(reverse('profiles_profile_detail',
                              kwargs={ 'username': request_user.username }))
@csrf_exempt
@requires_csrf_token
@login_required
def reactivate(request, wiki_url, next=None):
    """ Uncancel a article """
    (article, path, err) = fetch_from_url(request, wiki_url)
    if err:
        return err
    request_user = request.user
    # Check write permissions
    perm_err = check_permissions(request, article, check_write=True, check_locked=True)
    if perm_err:
        return perm_err
    if article.reactivate(request_user):
        """notify all concerned users by the object by the new comment"""
        #users_tonotify = ToNotify.objects.filter(article=article).exclude(user=request_user)
        #for user_tonotify in users_tonotify:
            #user = user_tonotify.user
            #notification.send([user], "article_reactivated", {'article': article, 'user':request_user,})
        #set stats
    if request.is_ajax():
        json_response = simplejson.dumps({
                'success': True,})
        return HttpResponse(json_response, mimetype="application/json")
    return  HttpResponseRedirect(reverse(next, args=(article.get_url(),)))

@login_required
def append_to(request, parent_id, child_id):
    """ append a cal to a parent cal """
    parent = Article.active.get(pk=parent_id)
    child = Article.active.get(pk=child_id)
    if parent:
        perm_err = check_permissions(request, parent.article, check_write=True)
        if perm_err:
            return perm_err
    if child:
        perm_err = check_permissions(request, child.article, check_write=True)
        if perm_err:
            return perm_err
    # Ensure doesn't already appended or it's child of the current one
    if (parent.parent == child):
        #the child is currently the parent of the future parent
        parent.parent = child.parent
        child.parent = parent
        parent.save()
        child.save()
    elif (child.parent == parent):
        #the child parent is the same future parent nothing to do then
        return
    else :
        #the parent and the child aren't related
        child.parent = parent
        child.save()

@login_required
def set_parent(request, wiki_url, template_name=None, next=None):
    """ add related cals """
    (article, path, err) = fetch_from_url(request, wiki_url)
    if err:
        return err

    # Check write permissions
    perm_err = check_permissions(request, article, check_write=True, check_locked=True)
    if perm_err:
        return perm_err
    request_user = request.user
    if request.method == 'POST':
        f = ParentForm(request.POST)
        if f.is_valid():
            parent = f.cleaned_data['parent'][0]
            article.set_parent(parent)
            if not request.is_ajax():
                return HttpResponseRedirect(reverse(next, args=(article.get_url(),)))
            response = ({'success':'True'})
        else:
            response = errors_as_json(f)
        if request.is_ajax():
            json = simplejson.dumps(response, ensure_ascii=False)
            return HttpResponse(json, mimetype="application/json")
    else:
        parent_title = article.parent.title + ','
        parent_id = str(article.parent.id) + ','
        f = ParentForm({'parent': parent_id,
                      })
    c = RequestContext(request, {'wiki_form': f,
                                 'wiki_write': True,
                                 'wiki_read': True,
                                 'wiki_article': article,
                                 'lock': True,
                                 'lock_url': reverse('lock_version', args=[article.id]),
                                 'unlock_url': reverse('unlock_version', args=[article.id]),
                                 'parent_title' : parent_title,
                                 'wiki_attachments_write': article.can_attach(request_user),
                                 })

    return render_to_response(template_name, c)

@login_required
def add_related(request, wiki_url, template_name=None, next=None):
    """ add related cals """
    (article, path, err) = fetch_from_url(request, wiki_url)
    if err:
        return err

    # Check write permissions
    perm_err = check_permissions(request, article, check_write=True, check_locked=True)
    if perm_err:
        return perm_err

    if request.method == 'POST':
        f = RelativeForm(request.POST)
        if f.is_valid():
            relatives = f.cleaned_data['relatives']
            article.edit_relatives(relatives)
            if not request.is_ajax():
                return HttpResponseRedirect(reverse(next, args=(article.get_url(),)))
            response = ({'success':'True'})
        else:
            response = errors_as_json(f)
        if request.is_ajax():
            json = simplejson.dumps(response, ensure_ascii=False)
            return HttpResponse(json, mimetype="application/json")
    else:
        relatives_title = ''
        relatives_id = ''
        for al in article.related.all():
            relatives_title = relatives_title + al.title + ','
            relatives_id = relatives_id + str(al.id) + ','
        f = RelativeForm({'relatives': relatives_id,
                      })
    c = RequestContext(request, {'wiki_form': f,
                                 'wiki_write': True,
                                 'wiki_read': True,
                                 'wiki_article': article,
                                 'lock': True,
                                 'lock_url': reverse('lock_version', args=[article.id]),
                                 'unlock_url': reverse('unlock_version', args=[article.id]),
                                 'relatives_title' : relatives_title,
                                 'wiki_attachments_write': article.can_attach(request.user),
                                 })

    return render_to_response(template_name, c)

@login_required
def add_attachment(request,wiki_url, template_name=None, next=None):
    """ add related cals """
    (article, path, err) = fetch_from_url(request, wiki_url)
    if err:
        return err

    # Check write permissions
    perm_err = check_permissions(request, article, check_write=True, check_locked=True)
    if perm_err:
        return perm_err
    request_user = request.user
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            Attachment(picture=form.cleaned_data['picture'], article = article, uploaded_by = request_user).save()
            if not request.is_ajax():
                return HttpResponseRedirect(reverse(next, args=(article.get_url(),)))
            response = {'success':True}
        else:
            response = errors_as_json(form)
        if request.is_ajax():
            json = simplejson.dumps(response, ensure_ascii=False)
            return HttpResponse(json, mimetype="application/json")
    else:
        form = AttachmentForm()
    c = RequestContext(request, {'wiki_form': form,
                                 'wiki_write': True,
                                 'wiki_read': True,
                                 'wiki_article': article,
                                 'lock': True,
                                 'lock_url': reverse('lock_version', args=[article.id]),
                                 'unlock_url': reverse('unlock_version', args=[article.id]),
                                 'wiki_attachments_write': article.can_attach(request_user),
                                 })

    return render_to_response(template_name, c)

def tree_view(request, wiki_url, template_name=None):
    """ display a tree for article children"""
    (article, path, err) = fetch_from_url(request, wiki_url)
    if err:
        return err

    # Check write permissions
    perm_err = check_permissions(request, article, check_read=True,)
    if perm_err:
        return perm_err
    request_user = request.user
    wiki_read, wiki_write = get_permissions(request, article)
    c = RequestContext(request, {
                                     'wiki_write': wiki_write,
                                     'wiki_read': wiki_read,
                                     'wiki_article': article,
                                     'wiki_attachments_write': article.can_attach(request_user),
                                     })

    return render_to_response(template_name, c)

@login_required
def articles_titles(request):
    """ return a json object containing related people names """
    q = request.GET['q'];
    list_titles = []

    articles = Article.active.all().filter(title__icontains=q)
    for article in articles:
        name = {
               'value' : article.id,
               'name' : article.title,
               }
        list_titles.append(name)

    json_cals = simplejson.dumps(list_titles, ensure_ascii=False)
    return HttpResponse(json_cals, content_type='application/javascript; charset=utf-8')
