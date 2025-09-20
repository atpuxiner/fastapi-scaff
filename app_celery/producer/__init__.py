"""
生产者
"""
from app_celery import make_celery

celery_app = make_celery()
