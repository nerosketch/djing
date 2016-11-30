from django.test import TestCase
from django.contrib.auth.models import User

import models


class PaysTest(TestCase):
    def setUp(self):
        self.msg = models.PrivateMessages.objects.create(
            sender=User.objects.all()[0],
            recepient=User.objects.all()[0],
            text='test init text'
        )

    def tearDown(self):
        models.PrivateMessages.objects.all().delete()

    def check_ret_msgs(self):
        """check return messages"""
        request = self.factory.get('/message/')
        self.assertIsInstance(models.PrivateMessages.objects.get_my_messages(request), int, 'checking ret type')
        self.assertGreater(models.PrivateMessages.objects.get_my_messages(request), 0, 'checking msg count')
