"""Celery worker configuration"""
# pylint: disable=C0103
from __future__ import absolute_import

import logging
import os

import celery
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lutrisweb.settings.local')

app = Celery('lutrisweb')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@celery.signals.after_setup_logger.connect
def on_after_setup_logger(**_kwargs):
    """Make sure the loggers propagate"""
    logger = logging.getLogger('celery')
    logger.propagate = True
    logger = logging.getLogger('celery.app.trace')
    logger.propagate = True
