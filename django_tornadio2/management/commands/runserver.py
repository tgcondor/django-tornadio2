# Copyright (c) 2012 TitanFile Inc. <https://www.titanfile.com>
#
# Author: Tony Abou-Assaleh <taa@titanfile.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler

from django_tornadio2.socket import BaseSocket
from django_tornadio2.loader import load_classes, _get_class
from django_tornadio2.loader import mixin

from optparse import make_option

from tornado.web import Application
from tornado.web import FallbackHandler
from tornado.web import RedirectHandler
from tornado.web import StaticFileHandler
from tornado.wsgi import WSGIContainer
from tornadio2 import TornadioRouter
from tornadio2 import SocketServer

from collections import defaultdict
import logging
import os

logger = logging.getLogger('tornadio2.server')

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete poll instead of closing it',
        ),
    )
    help = 'Start a Tornado/TornadIO2 server.'
    args = '[optional port number]'

    def handle(self, *args, **options):
        if settings.DEBUG:
            logger.setLevel(logging.DEBUG)

        if len(args) > 1:
            raise CommandError('Usage is runserver_tornadio2 %s' % self.args)

        if len(args) == 1:
            if ':' in args[0]:
                addr, port = args[0].split(':')
            else:
                port = args[0]
        else:
            port = getattr(settings, 'SOCKETIO_PORT', 8000)

        # Setup event handlers
        for Cls in load_classes(getattr(settings,'SOCKETIO_CLASSES', [])):
            mixin(BaseSocket, Cls)

        os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
        wsgi_app = get_wsgi_application()
        app_handler = WSGIContainer(StaticFilesHandler(wsgi_app))
        router = TornadioRouter(BaseSocket, {
            'enabled_protocols': [
                'websocket',
                'xhr-polling',
                'htmlfile'
            ]})

        if not hasattr(settings, 'SOCKETIO_GLOBALS'):
            settings.SOCKETIO_GLOBALS = {}

        settings.SOCKETIO_GLOBALS['server'] = router.urls[0][2]['server']
        # A map of user IDs to their active connections.
        settings.SOCKETIO_GLOBALS['connections'] = defaultdict(set)

        tornado_routes = []
        for url, path in getattr(settings, 'SOCKETIO_ROUTES', []):
            cls = _get_class(path, object)
            tornado_routes.append((url, cls))

        application = Application(
            router.urls + tornado_routes + [
                # Uncomment next line to handle static files through Tornado rather than Django or externally.
                #(r'/static/(.*)', StaticFileHandler, {'path': settings.STATICFILES_DIRS[0]}),
                (r'/admin$', RedirectHandler, {'url': '/admin/', 'permanent': True}),
                # You probably want to comment out the next line if you have a login form.
                (r'/accounts/login/.*', RedirectHandler, {'url': '/admin/', 'permanent': False}),
                (r'.*', FallbackHandler, {'fallback': app_handler}),
            ],
            #flash_policy_port = 843,
            #flash_policy_file = 'flashpolicy.xml',  # TODO: Do we need this? TAA - 2012-03-07.
            socket_io_port = port,
            xsrf_cookies = False,
            debug = settings.DEBUG
        )
        ssl_options = getattr(settings, 'SOCKETIO_SSL_OPTIONS', {})
        if ssl_options:
            SocketServer(application, ssl_options = ssl_options)
        else:
            SocketServer(application)

