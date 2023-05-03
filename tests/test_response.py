"""
This module provides test for json_response().
"""
import pytest
from flask_json import json_response


@pytest.mark.usefixtures('app_request')
class TestResponse(object):
    # Test: simple json_response() call.
    def test_simple(self):
        r = json_response()
        assert r.status_code == 200
        assert r.mimetype == 'application/json'

        # Set custom HTTPS status.
        r = json_response(status_=400)
        assert r.status_code == 400

        # Response will contains status by default.
        r = json_response(some='val', data=4)
        assert r.status_code == 200
        assert r.json == {'status': 200, 'some': 'val', 'data': 4}

    # Test: disable HTTP status field.
    def test_simple_no_status(self, app):
        app.config['JSON_ADD_STATUS'] = False
        r = json_response(some='val', data=42)
        assert r.json == {'some': 'val', 'data': 42}

    # Test: add_status_ param.
    def test_simple_status_param(self, app):
        app.config['JSON_ADD_STATUS'] = True
        r = json_response(some='val', data=42, add_status_=False)
        assert r.json == {'some': 'val', 'data': 42}

        app.config['JSON_ADD_STATUS'] = False
        r = json_response(some='val', data=42, add_status_=True)
        assert r.json == {'some': 'val', 'data': 42, 'status': 200}

    # Test: custom HTTP status field name.
    def test_custom_field_name(self, app):
        app.config['JSON_STATUS_FIELD_NAME'] = 'http_status'
        r = json_response()
        assert r.status_code == 200
        assert r.mimetype == 'application/json'
        assert r.json == {'http_status': 200}

        # Also if input data has key with the same name then it will be used
        # instead of HTTP status code.
        r = json_response(http_status='my value')
        assert r.status_code == 200
        assert r.json == {'http_status': 'my value'}

        # Let's change HTTPS status too.
        # See json_response() docs for more info.
        r = json_response(400, http_status='my value')
        assert r.status_code == 400
        assert r.json == {'http_status': 'my value'}

    # Test: custom headers in response.
    # One way to add custom headers is dict.
    def test_with_headers_dict(self):
        hdr = {'MY-HEADER': 'my value', 'X-HEADER': 42}
        r = json_response(headers_=hdr)
        assert r.status_code == 200
        assert r.mimetype == 'application/json'

        # There must be at least Content-Type, Content-Length and
        # our 2 extra headers.
        assert r.headers.get('Content-Type') == 'application/json'
        assert r.headers.get('MY-HEADER') == 'my value'
        assert r.headers.get('X-HEADER', type=int) == 42

    # Test: custom headers in response.
    # Another way to add custom headers is iterable.
    def test_with_headers_tuple(self):
        hdr = (('MY-HEADER', 'my value'), ('X-HEADER', 42))
        r = json_response(headers_=hdr)
        assert r.status_code == 200
        assert r.mimetype == 'application/json'
        assert r.headers.get('Content-Type') == 'application/json'
        assert r.headers.get('MY-HEADER') == 'my value'
        assert r.headers.get('X-HEADER', type=int) == 42

    # Test: if both data_ and kwargs are set.
    def test_params_both(self):
        r = json_response(data_={'x': 'y'}, val=1)
        assert r.status_code == 200
        assert r.json == {'status': 200, 'x': 'y', 'val': 1}

    # Test: if both data_ and kwargs are set but data_ is not a dict.
    def test_params_both_non_dict(self):
        with pytest.raises(AssertionError):
            json_response(data_=1, val=1)

    # Test: pass values via 'data_'.
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_data_param(self):
        r = json_response(data_=1)
        assert r.json == 1

        r = json_response(data_=[1, '2'])
        assert r.json == [1, '2']

        # No status is set if data_ is specified.
        r = json_response(data_=1, add_status_=True)
        assert r.json == 1

        # Works like you called with kwargs json_response(one=1, two='2').
        r = json_response(data_=dict(one=1, two='2'), add_status_=False)
        assert r.json == dict(one=1, two='2')

        r = json_response(data_=dict(one=1, two='2'), add_status_=True)
        assert r.json == dict(one=1, two='2', status=200)

        r = json_response(400, data_=dict(one=1, two='2'), add_status_=True)
        assert r.json == dict(one=1, two='2', status=400)

        hdr = (('MY-HEADER', 'my value'),)
        r = json_response(headers_=hdr, data_=dict(one=1, two='2'),
                          add_status_=True)
        assert r.json == dict(one=1, two='2', status=200)
        assert r.headers.get('MY-HEADER') == 'my value'
