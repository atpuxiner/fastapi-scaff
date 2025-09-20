import unittest

from app_celery.producer.publisher import publish


class TestPublisher(unittest.TestCase):

    def test_publish_aping(self):
        publish("aping", text="这是一个测试任务")
