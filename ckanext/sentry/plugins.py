# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import logging

import sentry_sdk
from flask import Blueprint
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware
from sentry_sdk.integrations.logging import SentryHandler
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.rq import RqIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from ckan import plugins


log = logging.getLogger(__name__)


CONFIG_FROM_ENV_VARS = {
    'sentry.dsn': 'CKAN_SENTRY_DSN',  # Alias for SENTRY_DSN, used by raven
    'sentry.configure_logging': 'CKAN_SENTRY_CONFIGURE_LOGGING',
    'sentry.log_level': 'CKAN_SENTRY_LOG_LEVEL',
}


class SentryPlugin(plugins.SingletonPlugin):
    '''A simple plugin that add the Sentry middleware to CKAN'''
    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    # IMiddleware

    def make_error_log_middleware(self, app, config):

        for option in CONFIG_FROM_ENV_VARS:
            from_env = os.environ.get(CONFIG_FROM_ENV_VARS[option], None)
            if from_env:
                config[option] = from_env
        if not config.get('sentry.dsn') and os.environ.get('SENTRY_DSN'):
            config['sentry.dsn'] = os.environ['SENTRY_DSN']

        if plugins.toolkit.asbool(config.get('sentry.configure_logging')):
            self._configure_logging(config)

        log.debug('Adding Sentry middleware...')
        sentry_sdk.init(dsn=config.get('sentry.dsn'),
                        integrations=[FlaskIntegration(), RqIntegration(), RedisIntegration()],
                        environment=config.get('sentry.environment', ""),
                        traces_sample_rate=0.2)
        SentryWsgiMiddleware(app)
        return app

    @staticmethod
    def _configure_logging(config):
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
            logger.setLevel(sentry_log_level)

        log.debug('Setting up Sentry logger with level {0}'.format(
            sentry_log_level))

    # IBlueprint
    def get_blueprint(self):

        def _trigger_error():
            division_by_zero = 1 / 0  # noqa

        # Create Blueprint for plugin
        blueprint = Blueprint(self.name, self.__module__)

        # Add plugin url rules to Blueprint object
        blueprint.add_url_rule(u'/debug-sentry', view_func=_trigger_error)

        return blueprint


    # IConfigurer
    def update_config(self, config):
        plugins.toolkit.add_template_directory(config, 'templates')
        plugins.toolkit.add_resource('assets', 'sentry')

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_sentry_config': get_sentry_config
        }

def get_sentry_config():
    return {
        "dsn": plugins.toolkit.config.get('sentry.dsn', ""),
        "environment": plugins.toolkit.config.get('sentry.environment', "")
    }