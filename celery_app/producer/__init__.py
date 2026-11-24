"""
生产者
"""

from celery_app import make_celery

app = make_celery()
