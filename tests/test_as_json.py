"""
This module provides tests for @as_json() decorator.
"""
import pytest
from flask import Response
from flask_json import json_response, _normalize_view_tuple, as_json


@pytest.mark.usefixtures('app_request')
class TestAsJson(object):
    # @as_json uses _normalize_view_tuple() internally to convert wrapped view's
    # return value to expected format.
    # This method tests various return values for _normalize_view_tuple().
    def test_normalize_view_tuple(self):
        # Test if view returns (dict, status, headers).
        data, status, headers = _normalize_view_tuple((dict(), 200, []))
        assert isinstance(data, dict)
        assert isinstance(status, int)
        assert isinstance(headers, list)

        data, status, headers = _normalize_view_tuple((dict(), 200, {}))
        assert isinstance(data, dict)
        assert isinstance(status, int)
        assert isinstance(headers, dict)

        # Test if view returns (dict, ).
        data, status, headers = _normalize_view_tuple((dict(), ))
        assert isinstance(data, dict)
        assert status is None
        assert headers is None

        # Test if view returns (dict, headers, status).
        data, status, headers = _normalize_view_tuple((dict(), [], 1))
        assert isinstance(data, dict)
        assert isinstance(status, int)
        assert isinstance(headers, list)

        # Test if view returns (dict, headers).
        data, status, headers = _normalize_view_tuple((dict(), []))
        assert isinstance(data, dict)
        assert status is None
        assert isinstance(headers, list)

        # Test if view returns (dict, status).
        data, status, headers = _normalize_view_tuple((dict(), 2))
        assert isinstance(data, dict)
        assert isinstance(status, int)
        assert headers is None

        # Test if view returns (list, status).
        data, status, headers = _normalize_view_tuple(([], 2))
        assert isinstance(data, list)
        assert isinstance(status, int)
        assert headers is None

        # Test if view returns (list, status, headers).
        data, status, headers = _normalize_view_tuple(([], 200, []))
        assert isinstance(data, list)
        assert isinstance(status, int)
        assert isinstance(headers, list)

    # Test common use case: convert dict return value to JSON response.
    def test_simple(self):
        @as_json
        def view1():
            """Doc"""
            return dict(value=1)

        # Just to make sure decorator is correctly wraps a function.
        assert view1.__doc__ == 'Doc'
        assert view1.__name__ == 'view1'

        r = view1()
        assert r.status_code == 200
        assert r.json == {'status': 200, 'value': 1}

    # Test: convert dict return value to JSON response with custom HTTP status.
    def test_status(self):
        @as_json
        def view1():
            return dict(value=1), 401

        r = view1()
        assert r.status_code == 401
        assert r.json == {'status': 401, 'value': 1}

    # Test: convert dict return value to JSON response with custom HTTP header.
    def test_header(self):
        @as_json
        def view1():
            return dict(value=1), dict(MY='hdr')

        r = view1()
        assert r.status_code == 200
        assert r.json == {'status': 200, 'value': 1}

        assert r.headers.get('Content-Type') == 'application/json'
        assert r.headers.get('MY') == 'hdr'

    # Test: convert dict return value to JSON response with custom status
    # and header (combination of above tests).
    def test_status_header(self):
        @as_json
        def view1():
            return dict(value=1), 400, dict(MY='hdr')

        r = view1()
        assert r.status_code == 400
        assert r.json == {'status': 400, 'value': 1}

        assert r.headers.get('Content-Type') == 'application/json'
        assert r.headers.get('MY') == 'hdr'

    # Test: Same as before but different order of values.
    def test_header_status(self):
        @as_json
        def view1():
            return dict(value=1), dict(MY='hdr'), 400

        r = view1()
        assert r.status_code == 400
        assert r.json == {'status': 400, 'value': 1}

        assert r.headers.get('Content-Type') == 'application/json'
        assert r.headers.get('MY') == 'hdr'

    # Test: None payload.
    def test_none_single(self):
        @as_json
        def view1():
            return None

        r = view1()
        assert r.status_code == 200
        assert r.json == {'status': 200}
        assert r.headers.get('Content-Type') == 'application/json'

    # Test: None payload + status.
    def test_none_with_status(self):
        @as_json
        def view1():
            return None, 400

        r = view1()
        assert r.status_code == 400
        assert r.json == {'status': 400}

    # Test: None payload + headers.
    def test_none_with_headers(self):
        @as_json
        def view():
            return None, dict(MY='hdr')

        r = view()
        assert r.status_code == 200
        assert r.json == {'status': 200}
        assert r.headers.get('Content-Type') == 'application/json'
        assert r.headers.get('MY') == 'hdr'

    # Test: None payload + status + headers.
    def test_none_with_status_headers(self):
        @as_json
        def view():
            return None, 400, dict(MY='hdr')

        r = view()
        assert r.status_code == 400
        assert r.json == {'status': 400}
        assert r.headers.get('Content-Type') == 'application/json'
        assert r.headers.get('MY') == 'hdr'

    # Test: None payload + headers + status.
    def test_none_with_headers_status(self):
        @as_json
        def view():
            return None, dict(MY='hdr'), 401

        r = view()
        assert r.status_code == 401
        assert r.json == {'status': 401}
        assert r.headers.get('Content-Type') == 'application/json'
        assert r.headers.get('MY') == 'hdr'

    # Test: if a view returns Flask response.
    def test_with_response(self):
        @as_json
        def view():
            return Response()

        # It must fail because we accept only JSON response in @as_json.
        with pytest.raises(AssertionError):
            view()

    # Test: if a view returns json_response().
    def test_with_json_response(self):
        @as_json
        def view():
            return json_response(val=12)

        r = view()
        assert r.status_code == 200
        assert r.headers.get('Content-Type') == 'application/json'
        assert r.json == {'status': 200, 'val': 12}

    # Test: invalid return value.
    # See also comments for _normalize_view_tuple().
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_invalid(self):
        @as_json
        def view1():
            return object()  # not supported.

        with pytest.raises(TypeError) as e:
            view1()
        assert str(e.value).endswith(' is not JSON serializable')

    # Test: return integer
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_non_dict_int(self):
        @as_json
        def view1():
            return 1

        r = view1()
        assert r.status_code == 200
        assert r.json == 1

    # Test: return array
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_non_dict_array(self):
        @as_json
        def view1():
            return [1, '2']

        r = view1()
        assert r.status_code == 200
        assert r.json == [1, '2']

    # Test: return array
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_non_dict_empty_array(self):
        @as_json
        def view1():
            return []

        r = view1()
        assert r.status_code == 200
        assert r.json == []

    # Test: return array with status
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_non_dict_array_status(self):
        @as_json
        def view1():
            return [1, '2'], 400

        r = view1()
        assert r.status_code == 400
        assert r.json == [1, '2']

    # Test: convert integer to JSON response with custom HTTP header.
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_non_dict_int_header(self):
        @as_json
        def view1():
            return 1, dict(MY='hdr')

        r = view1()
        assert r.status_code == 200
        assert r.json == 1

        assert r.headers.get('Content-Type') == 'application/json'
        assert r.headers.get('MY') == 'hdr'

    # Test: convert array to JSON response with custom status and header.
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_non_dict_array_status_header(self):
        @as_json
        def view1():
            return [1, '2'], 400, dict(MY='hdr')

        r = view1()
        assert r.status_code == 400
        assert r.json == [1, '2']

        assert r.headers.get('Content-Type') == 'application/json'
        assert r.headers.get('MY') == 'hdr'
