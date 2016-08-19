from django.db import models


class Dot(models.Model):
    title = models.CharField(max_length=64)
    posX = models.FloatField()
    posY = models.FloatField()

    def __unicode__(self):
        return self.title
