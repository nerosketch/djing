# -*- coding:utf-8 -*-
import os
import time
import hashlib

from django.db import models
from PIL import Image
from django.conf import settings

BASE_DIR = getattr(settings, 'BASE_DIR', '.')


class Photo(models.Model):
    image = models.ImageField(width_field='wdth', height_field='heigt')
    wdth = models.PositiveSmallIntegerField(null=True, blank=True, editable=False, default="759")
    heigt = models.PositiveSmallIntegerField(null=True, blank=True, editable=False)

    def __str__(self):
        return "{0}".format(self.image)

    def big(self):
        return self.image.url

    def min(self):
        pth = self.image.url.split('/')[-1:][0]
        return "/media/min/%s" % pth

    def save(self, *args, **kwargs):
        if not self.image:
            return
        super(Photo, self).save(*args, **kwargs)
        im = Image.open(self.image.path)
        im.thumbnail((759, 759), Image.ANTIALIAS)

        hs = hashlib.md5(str(time.time()).encode()).hexdigest()
        ext = self.image.path.split('.')[1:][0]
        path = "%s/media" % BASE_DIR
        fname = "%s/%s.%s" % (path, hs, ext)
        if not os.path.exists(path):
            os.makedirs(path)
        if not os.path.exists(path + '/min'):
            os.makedirs(path + '/min')
        im.save(fname)
        os.remove(self.image.path)
        self.image = "%s.%s" % (hs, ext)
        super(Photo, self).save(*args, **kwargs)

        # class Meta:
        #    unique_together = (('image',),)


def resize_image(sender, instance, **kwargs):
    if not kwargs['created']:
        im = Image.open(instance.image.path)
        im.thumbnail((200, 121), Image.ANTIALIAS)
        pth = instance.image.path.split('/')[-1:][0]
        fullpath = "%s/media/min/%s" % (BASE_DIR, pth)
        im.save(fullpath)


def post_delete_photo(sender, instance, **kwargs):
    min_fname = instance.image.path.split('/')[-1:][0]
    try:
        os.remove('%s/media/min/%s' % (BASE_DIR, min_fname))
        os.remove(instance.image.path)
    except OSError:
        pass


models.signals.post_save.connect(resize_image, sender=Photo)
models.signals.post_delete.connect(post_delete_photo, sender=Photo)
