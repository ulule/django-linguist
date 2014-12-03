# -*- coding: utf-8 -*-
import logging
from optparse import make_option

from django.core import management
from django.core.management.base import BaseCommand

logger = logging.getLogger('example.fixtures')


class Command(BaseCommand):
    """
    Creates fixtures.
    """
    help = u'Create fixtures'

    option_list = BaseCommand.option_list + (
        make_option('--flushdb',
            action='store_true',
            dest='flushdb'),)

    def handle(self, *args, **options):
        self.flushdb = options.get('flushdb')
        self._pre_tasks()
        print('Hello, You.')

    def _pre_tasks(self):
        if self.flushdb:
            management.call_command('flush', verbosity=0, interactive=False)
            logger.info('Flushed database')
