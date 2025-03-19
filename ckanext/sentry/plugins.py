# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import logging

import sentry_sdk
from flask import Blueprint
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware
from sentry_sdk.integrations.logging import LoggingIntegration

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
    plugins.implements(plugins.IClick)

    # IMiddleware

    def make_error_log_middleware(self, app, config):

        for option in CONFIG_FROM_ENV_VARS:
            from_env = os.environ.get(CONFIG_FROM_ENV_VARS[option], None)
            if from_env:
                config[option] = from_env
        if not config.get('sentry.dsn') and os.environ.get('SENTRY_DSN'):
            config['sentry.dsn'] = os.environ['SENTRY_DSN']

        sentry_log_levels = {
            'level': logging.INFO,
            'event_level': logging.ERROR
        }

        if plugins.toolkit.asbool(config.get('sentry.configure_logging')):
            sentry_log_levels['level'] = config.get('sentry.log_level', logging.INFO)
            sentry_log_levels['event_level'] = config.get('sentry.event_level', logging.ERROR)

        log.debug('Adding Sentry middleware...')
        sentry_sdk.init(dsn=config.get('sentry.dsn'),
                        integrations=[LoggingIntegration(**sentry_log_levels)],
                        environment=config.get('sentry.environment', ""),
                        traces_sample_rate=float(config.get('sentry.traces_sample_rate', 0.2)),
                        profiles_sample_rate=float(config.get('sentry.profiles_sample_rate', 0.2)))
        app = SentryWsgiMiddleware(app)
        return app

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
            'get_sentry_config': get_sentry_config,
            'get_sentry_loader_script': get_sentry_loader_script
        }

    # IClick

    def get_commands(self):
        import click

        @click.group(short_help="Debug commands for sentry.")
        def sentry():
            'Debug commands for sentry.'
            pass

        @sentry.command(short_help="Produces an error.")
        def debug():
            division_by_zero = 1 / 0  # noqa
        return [sentry]


def get_sentry_config():
    return {
        "environment": plugins.toolkit.config.get('sentry.environment', ""),
        "tracesSampleRate": plugins.toolkit.config.get('sentry.traces_sample_rate', '0.2')
    }

def get_sentry_loader_script():
    return plugins.toolkit.config.get('sentry.loader_script')
