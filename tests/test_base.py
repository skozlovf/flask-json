"""
This module provides tests for JsonTestResponse and additional test to
make sure what request.get_json() call works and can convert data to JSON
(it's probably more integration test than unit test to see if Flask and part
of Flask-JSON works together).
"""
from .common import *
from flask import request
from flask_json import json_response, JsonTestResponse


class TestBase(CommonTest):
    # CommonTest setups Flask to use JsonTestResponse, so here we test if
    # response class is JsonTestResponse and also access to it's json content.
    def test_response_class(self):
        r = json_response(one=12)
        assert_is_instance(r, JsonTestResponse)
        assert_dict_equal(r.json, dict(status=200, one=12))

        r = json_response(two='hello')
        assert_is_instance(r, JsonTestResponse)
        assert_equals(r.json['two'], 'hello')
        assert_equals(r.json['status'], 200)

    # Check if request.get_json() call works.
    def test_get_json(self):
        @self.app.route('/test', methods=['POST'])
        def endpoint():
            data = request.get_json()
            return json_response(**data)

        r = self.post_json('/test', dict(some=42))
        assert_equals(r.status_code, 200)
        assert_dict_equal(r.json, dict(status=200, some=42))
