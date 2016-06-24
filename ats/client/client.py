
import argparse
import configparser
import logging
import os
import stat
import subprocess

import cliff.app
import requests

# fix for 3.5
subprocess.mswindows = False


def urlpath(*parts):
    """
    There is no real equivalent in stdlib
    """
    return '/'.join(s.strip('/') for s in parts)


class DebugRequestsAction(argparse.Action):
    def __call__(self, *args, **kw):
        requests.packages.urllib3.add_stderr_logger()


class ClientApp(cliff.app.App):
    default_config_file = None

    def __init__(self, *args, **kw):
        # silence messages like 'Starting connection' coming from requests, that are logged with INFO
        logging.getLogger('requests.packages.urllib3').setLevel(logging.WARNING)
        super().__init__(*args, **kw)

    def build_option_parser(self, *args, **kw):
        parser = super().build_option_parser(*args, **kw)
        parser.add_argument(
            '--config',
            default=self.default_config_file,
            help='Configuration file (default: %(default)s)')
        parser.add_argument('--debug-requests',
                            help='Print request details',
                            nargs=0,
                            action=DebugRequestsAction)
        return parser

    def initialize_app(self, argv):
        if argv and argv[0] == 'help':
            return

        self.LOG.debug('Configuration file: %s', self.options.config)

        fpath = os.path.realpath(self.options.config)

        try:
            st_mode = os.stat(fpath).st_mode
        except FileNotFoundError:
            raise IOError('The configuration file %s was not found' % fpath)

        if st_mode & stat.S_IRGRP:
            raise IOError('The configuration file %s is group readable' % fpath)

        if st_mode & stat.S_IWGRP:
            raise IOError('The configuration file %s is group writable' % fpath)

        if st_mode & stat.S_IROTH:
            raise IOError('The configuration file %s is world readable' % fpath)

        if st_mode & stat.S_IWOTH:
            raise IOError('The configuration file %s is world writable' % fpath)

        self.config = configparser.ConfigParser()
        with open(fpath, 'r') as fin:
            self.config.read_file(fin)

        self.server_url = self.config['session']['server_url']

    def add_auth_options(self, parser):
        parser.add_argument('--as-user',
                            help='userid to impersonate')
        return parser

    def auth_header(self, parsed_args):
        user = parsed_args.as_user
        if not user:
            try:
                user = self.config['session']['user']
            except KeyError:
                self.LOG.debug('No user set')
                pass

        if user:
            return {'X-Auth-UserId': user}
        else:
            return {}

    def raise_for_status_verbose(self, response):
        """
        Calls raise_for_status but also prints the response body, which contains a
        detailed error message. Not done in the upstream requests packages because
        it may be too long, not exist at all, or be unprintable.

        https://github.com/kennethreitz/requests/issues/2402
        """
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            self.LOG.error(error.response.text)
            # XXX exception message gets printed twice
            raise

    def list2fields(self, objects):
        """
        Returns output for a Lister instance from a list of dictionaries
        """

        fields = set()
        for obj in objects:
            fields = fields.union(obj.keys())
        fields = sorted(fields)

        return fields, ([obj.get(f, '') for f in fields] for obj in objects)

    def url(self, *parts):
        return urlpath(self.server_url, *parts)

    def _requests_method(self, method, *parts, **kw):
        url = self.url(*parts)
        r = method(url, **kw)
        self.raise_for_status_verbose(r)
        return r

    def do_get(self, *parts, **kw):
        return self._requests_method(requests.get, *parts, **kw)

    def do_post(self, *parts, **kw):
        return self._requests_method(requests.post, *parts, **kw)

    def do_put(self, *parts, **kw):
        return self._requests_method(requests.put, *parts, **kw)

    def do_delete(self, *parts, **kw):
        return self._requests_method(requests.delete, *parts, **kw)
