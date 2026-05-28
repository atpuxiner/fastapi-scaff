import unittest

from app_celery.producer import publisher


class TestPublisher(unittest.TestCase):
    def test_publish_health(self):
        publisher.publish("health")
