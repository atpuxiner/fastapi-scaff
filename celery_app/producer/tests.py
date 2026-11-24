import unittest

from celery_app.producer import publisher


class TestPublisher(unittest.TestCase):
    def test_publish_health(self):
        publisher.publish("health")
