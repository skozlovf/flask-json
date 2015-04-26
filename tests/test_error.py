"""
This module provides tests for JsonError exception handing.
"""
from .common import *
from flask_json import JsonError


class TestJsonError(CommonTest):
    # Test: simple JsonError raising.
    # The rror must be converted to JSON response with HTTP 400 status.
    def test_simple(self):
        @self.app.route('/test')
        def endpoint():
            raise JsonError

        r = self.client.get('/test')
        assert_equals(r.status_code, 400)
        assert_dict_equal(r.json, {'status': 400})

        # Now disable HTTP status field in response.
        self.app.config['JSON_ADD_STATUS'] = False
        r = self.client.get('/test')
        assert_equals(r.status_code, 400)
        assert_dict_equal(r.json, {})

    # Test: JsonError with data.
    def test_with_data(self):
        @self.app.route('/test')
        def endpoint():
            raise JsonError(info='Some info')

        r = self.client.get('/test')
        assert_equals(r.status_code, 400)
        assert_dict_equal(r.json, {'status': 400, 'info': 'Some info'})

        # Check how it works with disabled HTTP status field in response.
        self.app.config['JSON_ADD_STATUS'] = False
        r = self.client.get('/test')
        assert_equals(r.status_code, 400)
        assert_dict_equal(r.json, {'info': 'Some info'})

    # Test: JsonError with custom headers.
    def test_with_headers(self):
        @self.app.route('/test')
        def endpoint():
            raise JsonError(headers_=dict(MY=123), status_=401, info='Info')

        r = self.client.get('/test')
        assert_equals(r.status_code, 401)
        assert_dict_equal(r.json, {'status': 401, 'info': 'Info'})
        assert_true(r.headers.get('Content-Length', type=int) > 0)
        assert_equals(r.headers.get('Content-Type'), 'application/json')
        assert_equals(r.headers.get('MY'), '123')

    # Test: JsonError handler.
    def test_handler(self):
        @self.app.route('/test')
        def endpoint():
            raise JsonError(info='Some info')

        # Just return error's info as HTTP 200.
        @self.ext.error_handler
        def handler(e):
            return e.data['info']

        r = self.client.get('/test')
        assert_equals(r.status_code, 200)

        # On python 3 Response.data is a byte object, so to compare we have to
        # convert it to unicode.
        data = r.data.decode('utf-8') if sys.version_info > (2, 7) else r.data
        assert_equals(data, 'Some info')
