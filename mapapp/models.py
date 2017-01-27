from django.db import models


class Dot(models.Model):
    title = models.CharField(max_length=127)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        db_table = 'dots'

    def __str__(self):
        return self.title
