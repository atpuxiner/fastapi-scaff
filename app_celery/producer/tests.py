import unittest

from app_celery.producer.publisher import publish


class TestPublisher(unittest.TestCase):

    def test_publish_ping(self):
        publish("ping")
