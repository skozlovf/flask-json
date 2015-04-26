"""
This module contains common parts for testing.
"""
from nose.tools import assert_equals, assert_true, raises

# To support python 2.6 tests we have to add few missing functions.
import sys
if sys.version_info < (2, 7):
    def assert_is(a, b):
        assert a is b

    def assert_is_not(a, b):
        assert a is not b

    def assert_is_none(a):
        assert a is None

    def assert_is_not_none(a):
        assert a is not None

    def assert_dict_equal(a, b):
        diff = set(a.iteritems()) - set(b.iteritems())
        assert not diff, 'dicts are different'

    def assert_is_instance(obj, cls):
        assert isinstance(obj, cls), '%s is not an instance of %s' % (obj, cls)
else:
    from nose.tools import (
        assert_is,
        assert_is_not,
        assert_is_none,
        assert_is_not_none,
        assert_dict_equal,
        assert_is_instance
    )

from flask import Flask, json
import flask_json


class CommonTest(object):
    """Common test class.

    It setups Flask application and Flask-JSON; also provides help method
    to send POST requests with JSON payload.

    Another feature is what this class pushes Flask's test request context
    on setup and pops it on teardown, so you don't need to use::

        with self.app.test_request_context():
            ...

    in test methods.
    """
    def setup(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.ext = flask_json.FlaskJSON(self.app)
        self.client = self.ext._app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def teardown(self):
        self.ctx.pop()

    def post_json(self, url, data, raw=False):
        """Helper method to send JSON POST requests.

        Usage:

            self.post_json('/some/url', dict(param=value))
            self.post_json('/some/url', '{"param": "value"}', raw=True)

        Args:
            url: Target URL.
            data: Request payload. It maybe a dict or string with raw content.
            raw: If ``True`` then do not convert ``data`` to JSON string and use
                 it as is.

        Returns:
            flask_json.JsonTestResponse
        """
        content = data if raw else json.dumps(data)
        headers = [
            ('Content-Type', 'application/json'),
            ('Content-Length', len(content))
        ]
        return self.client.post(url, headers=headers, data=content)
