# -*- coding:utf-8 -*-
from django.db import models
from djing.settings import BASE_DIR
import os
from PIL import Image
import time
import hashlib


class Photo(models.Model):
    image = models.ImageField(width_field='wdth', height_field='heigt')
    wdth = models.PositiveSmallIntegerField(null=True, blank=True, editable=False, default="759")
    heigt = models.PositiveSmallIntegerField(null=True, blank=True, editable=False)

    def __unicode__(self):
        return "{0}".format(self.image)

    def big(self):
        return self.image.url

    def min(self):
        pth = self.image.url.split('/')[-1:][0]
        return "/media/min/%s" % pth

    def save(self, *args, **kwargs):
        if not self.image:
            return

        super(Photo, self).save()

        im = Image.open(self.image.path)
        im.thumbnail((759, 759), Image.ANTIALIAS)

        hs = hashlib.md5(str(time.time())).hexdigest()
        ext = self.image.path.split('.')[1:][0]
        fname = "%s/media/%s.%s" % (BASE_DIR, hs, ext)

        im.save(fname)
        os.remove(self.image.path)
        self.image = "%s.%s" % (hs, ext)
        super(Photo, self).save()


    #class Meta:
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
