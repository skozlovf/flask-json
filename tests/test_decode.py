# -*- coding: utf-8 -*-
"""
This module provides tests for Flask-JSON decoder feature.
"""
from .common import *
from flask import request
from flask_json import json_response


class TestDecode(CommonTest):
    # Setup endpoint for testing.
    # We test request JSON decoding this way: the endpoint calls
    # request.get_json() and sends result data for testing.
    def setup(self):
        super(TestDecode, self).setup()

        @self.app.route('/test', methods=['POST'])
        def endpoint():
            data = request.get_json()
            return json_response(**data)

    # Test: invalid/malformed input JSON.
    # It must raise 'Not a JSON' error with HTTP 400 status code.
    def test_error(self):
        r = self.post_json('/test', data='bla', raw=True)
        assert_equals(r.status_code, 400)
        assert_dict_equal(r.json,
                          dict(status=400, description='Not a JSON.'))

    # Test: set custom error message for invalid/malformed request JSON.
    def test_custom_message(self):
        self.app.config['JSON_DECODE_ERROR_MESSAGE'] = 'WTF?'
        r = self.post_json('/test', data='bla', raw=True)
        assert_dict_equal(r.json,
                          dict(status=400, description='WTF?'))

    # Test: set empty error message for invalid/malformed request JSON.
    # This means disable error message at all in response.
    # But it still returns HTTP 400 error.
    def test_empty_message(self):
        self.app.config['JSON_DECODE_ERROR_MESSAGE'] = None
        r = self.post_json('/test', data='bla', raw=True)
        assert_dict_equal(r.json, dict(status=400))

    # Test: set custom decoder error handler.
    # It just returns predefined dict instead of raising an error.
    def test_custom_handler(self):
        @self.ext.invalid_json_error
        def handler(e):
            return dict(text='hello')

        self.app.config['JSON_DECODE_ERROR_MESSAGE'] = None
        r = self.post_json('/test', data='bla', raw=True)
        assert_dict_equal(r.json, dict(status=200, text='hello'))

    # Test: set decoder with no action (nothing is raised or returned).
    # On such situations Flask-JSON runs default action: raise 'Not a JSON'.
    def test_custom_handler_empty(self):
        @self.ext.invalid_json_error
        def handler2(e):
            pass

        self.app.config['JSON_DECODE_ERROR_MESSAGE'] = None
        r = self.post_json('/test', data='bla', raw=True)
        assert_dict_equal(r.json, dict(status=400))
