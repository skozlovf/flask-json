# -*- coding: utf-8 -*-
"""
This module provides tests for Flask-JSON decoder feature.
"""
import pytest
from flask import request
from flask_json import json_response


@pytest.fixture
def theapp(app):
    @app.route('/test', methods=['POST'])
    def endpoint():
        data = request.get_json()
        return json_response(**data)
    yield app


@pytest.mark.usefixtures('theapp')
class TestDecode(object):
    # Test: invalid/malformed input JSON.
    # It must raise 'Not a JSON' error with HTTP 400 status code.
    def test_error(self, client):
        r = client.post_json('/test', data='bla', raw=True)
        assert r.status_code == 400
        assert r.json == dict(status=400, description='Not a JSON.')

    # Test: set custom error message for invalid/malformed request JSON.
    def test_custom_message(self, app, client):
        app.config['JSON_DECODE_ERROR_MESSAGE'] = 'WTF?'
        r = client.post_json('/test', data='bla', raw=True)
        assert r.json == dict(status=400, description='WTF?')

    # Test: set empty error message for invalid/malformed request JSON.
    # This means disable error message at all in response.
    # But it still returns HTTP 400 error.
    def test_empty_message(self, app, client):
        app.config['JSON_DECODE_ERROR_MESSAGE'] = None
        r = client.post_json('/test', data='bla', raw=True)
        assert r.json == dict(status=400)

    # Test: set custom decoder error handler.
    # It just returns predefined dict instead of raising an error.
    def test_custom_handler(self, app, client):
        invalid_json_error = app.extensions['json'].invalid_json_error

        @invalid_json_error
        def handler(e):
            return dict(text='hello')

        app.config['JSON_DECODE_ERROR_MESSAGE'] = None
        r = client.post_json('/test', data='bla', raw=True)
        assert r.json == dict(status=200, text='hello')

    # Test: set decoder with no action (nothing is raised or returned).
    # On such situations Flask-JSON runs default action: raise 'Not a JSON'.
    def test_custom_handler_empty(self, app, client):
        invalid_json_error = app.extensions['json'].invalid_json_error

        @invalid_json_error
        def handler2(e):
            pass

        app.config['JSON_DECODE_ERROR_MESSAGE'] = None
        r = client.post_json('/test', data='bla', raw=True)
        assert r.json == dict(status=400)
