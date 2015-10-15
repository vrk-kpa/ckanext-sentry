# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
        from raven.contrib.pylons import Sentry

        log.debug('Adding Sentry middleware...')
        return Sentry(app, config)
