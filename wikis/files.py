# -*- coding: utf-8 -*-
def get_attachment_path(instance, filename):
    """Store file, appending new extension for added security"""
    dir = "uploads/%s/%s" % (instance.event.get_url()[:32], filename)
    return dir
