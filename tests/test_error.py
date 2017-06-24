"""
This module provides tests for JsonError exception handing.
"""
import sys
from flask_json import JsonError


class TestJsonError(object):
    # Test: simple JsonError raising.
    # The error must be converted to JSON response with HTTP 400 status.
    def test_simple(self, app, client):
        @app.route('/test')
        def endpoint():
            raise JsonError

        r = client.get('/test')
        assert r.status_code == 400
        assert r.json == {'status': 400}

        # Now disable HTTP status field in response.
        app.config['JSON_ADD_STATUS'] = False
        r = client.get('/test')
        assert r.status_code == 400
        assert r.json == {}

    # Test: JsonError with data.
    def test_with_data(self, app, client):
        @app.route('/test')
        def endpoint():
            raise JsonError(info='Some info')

        r = client.get('/test')
        assert r.status_code == 400
        assert r.json == {'status': 400, 'info': 'Some info'}

        # Check how it works with disabled HTTP status field in response.
        app.config['JSON_ADD_STATUS'] = False
        r = client.get('/test')
        assert r.status_code == 400
        assert r.json == {'info': 'Some info'}

    # Test: JsonError with custom headers.
    def test_with_headers(self, app, client):
        @app.route('/test')
        def endpoint():
            raise JsonError(headers_=dict(MY=123), status_=401, info='Info')

        r = client.get('/test')
        assert r.status_code == 401
        assert r.json == {'status': 401, 'info': 'Info'}
        assert r.headers.get('Content-Type') == 'application/json'
        assert r.headers.get('MY') == '123'

    # Test: JsonError handler.
    def test_handler(self, app, client):
        @app.route('/test')
        def endpoint():
            raise JsonError(info='Some info')

        error_handler = app.extensions['json'].error_handler

        # Just return error's info as HTTP 200.
        @error_handler
        def handler(e):
            return e.data['info']

        r = client.get('/test')
        assert r.status_code == 200

        # On python 3 Response.data is a byte object, so to compare we have to
        # convert it to unicode.
        data = r.data.decode('utf-8') if sys.version_info > (2, 7) else r.data
        assert data == 'Some info'
