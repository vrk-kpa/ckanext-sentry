# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from raven.contrib.pylons import Sentry
from raven.handlers.logging import SentryHandler

import logging

from ckan import plugins


log = logging.getLogger(__name__)


class SentryPlugin(plugins.SingletonPlugin):
    '''A simple plugin that add the Sentry middleware to CKAN'''
    plugins.implements(plugins.IMiddleware, inherit=True)

    def make_middleware(self, app, config):
        if plugins.toolkit.check_ckan_version('2.3'):
            return app
        else:
            return self.make_error_log_middleware(app, config)

    def make_error_log_middleware(self, app, config):

        if plugins.toolkit.asbool(config.get('sentry.configure_logging')):
            self._configure_logging(config)

        log.debug('Adding Sentry middleware...')
        return Sentry(app, config)

    def _configure_logging(self, config):
        '''
        Configure the Sentry log handler to the specified level

        Based on @rshk work on
        https://github.com/opendatatrentino/ckanext-sentry
        '''

        handler = SentryHandler(config.get('sentry.dsn'))
        handler.setLevel(logging.NOTSET)

        loggers = ['', 'ckan', 'ckanext', 'sentry.errors']
        sentry_log_level = config.get('sentry.log_level', logging.INFO)
        for name in loggers:
            logger = logging.getLogger(name)
            logger.addHandler(handler)
            if name == 'sentry.errors':
                logger.setLevel(sentry_log_level)

        log.debug('Setting up Sentry logger with level {0}'.format(
            sentry_log_level))
