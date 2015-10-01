"""
This module provides test for json_response().
"""
from .common import *
from flask_json import json_response


class TestResponse(CommonTest):
    # Test: simple json_response() call.
    def test_simple(self):
        r = json_response()
        assert_equals(r.status_code, 200)
        assert_equals(r.mimetype, 'application/json')

        # Set custom HTTPS status.
        r = json_response(status_=400)
        assert_equals(r.status_code, 400)

        # Response will contains status by default.
        r = json_response(some='val', data=4)
        assert_equals(r.status_code, 200)
        assert_dict_equal(r.json, {'status': 200, 'some': 'val', 'data': 4})

    # Test: disable HTTP status field.
    def test_simple_no_status(self):
        self.app.config['JSON_ADD_STATUS'] = False
        r = json_response(some='val', data=42)
        assert_dict_equal(r.json, {'some': 'val', 'data': 42})

    # Test: add_status_ param.
    def test_simple_status_param(self):
        self.app.config['JSON_ADD_STATUS'] = True
        r = json_response(some='val', data=42, add_status_=False)
        assert_dict_equal(r.json, {'some': 'val', 'data': 42})

        self.app.config['JSON_ADD_STATUS'] = False
        r = json_response(some='val', data=42, add_status_=True)
        assert_dict_equal(r.json, {'some': 'val', 'data': 42, 'status': 200})

    # Test: custom HTTP status field name.
    def test_custom_field_name(self):
        self.app.config['JSON_STATUS_FIELD_NAME'] = 'http_status'
        r = json_response()
        assert_equals(r.status_code, 200)
        assert_equals(r.mimetype, 'application/json')
        assert_dict_equal(r.json, {'http_status': 200})

        # Also if input data has key with the same name then it will be used
        # instead of HTTP status code.
        r = json_response(http_status='my value')
        assert_equals(r.status_code, 200)
        assert_dict_equal(r.json, {'http_status': 'my value'})

        # Let's change HTTPS status too.
        # See json_response() docs for more info.
        r = json_response(400, http_status='my value')
        assert_equals(r.status_code, 400)
        assert_dict_equal(r.json, {'http_status': 'my value'})

    # Test: custom headers in response.
    # One way to add custom headers is dict.
    def test_with_headers_dict(self):
        hdr = {'MY-HEADER': 'my value', 'X-HEADER': 42}
        r = json_response(headers_=hdr)
        assert_equals(r.status_code, 200)
        assert_equals(r.mimetype, 'application/json')

        # There must be at least Content-Type, Content-Length and
        # our 2 extra headers.
        assert_equals(r.headers.get('Content-Type'), 'application/json')
        assert_true(r.headers.get('Content-Length', type=int) > 0)
        assert_equals(r.headers.get('MY-HEADER'), 'my value')
        assert_equals(r.headers.get('X-HEADER', type=int), 42)

    # Test: custom headers in response.
    # Another way to add custom headers is iterable.
    def test_with_headers_tuple(self):
        hdr = (('MY-HEADER', 'my value'), ('X-HEADER', 42))
        r = json_response(headers_=hdr)
        assert_equals(r.status_code, 200)
        assert_equals(r.mimetype, 'application/json')
        assert_equals(r.headers.get('Content-Type'), 'application/json')
        assert_true(r.headers.get('Content-Length', type=int) > 0)
        assert_equals(r.headers.get('MY-HEADER'), 'my value')
        assert_equals(r.headers.get('X-HEADER', type=int), 42)
