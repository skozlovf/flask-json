"""
This module provides tests for @as_json_p() decorator.
"""
import sys
import pytest
from werkzeug.exceptions import BadRequest
from flask import Response, json
from flask_json import json_response, _json_p_handler, as_json_p


@pytest.fixture
def theapp(app):
    # Disable pretty print to have smaller result string
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    # Force status field to test if it will be added to JSONP response.
    # It must drop status field.
    app.config['JSON_ADD_STATUS'] = True

    # Initial config for the @as_json_p
    app.config['JSON_JSONP_STRING_QUOTES'] = True
    app.config['JSON_JSONP_OPTIONAL'] = True
    app.config['JSON_JSONP_QUERY_CALLBACKS'] = ['callback', 'jsonp']
    return app


# Helper function to make a request.
def req(app, *args, **kwargs):
    return app.test_request_context(*args, **kwargs)


class TestAsJsonP(object):
    # Test: required callback in the URL query.
    def test_handler_missing_callback_required(self, app):
        with req(app, '/?param=1'):
            # It must fail since callback name is not provided
            # in the 'callback' query param.
            with pytest.raises(BadRequest):
                _json_p_handler('x', callbacks=['callback', 'foo'],
                                optional=False)

    # Test: optional callback in the URL query.
    # It must return regular response if callback name is not provided.
    def test_handler_missing_callback_optional(self, app):
        with req(app, '/?param=1'):
            rv = _json_p_handler({'x': 1},
                                 callbacks=['callback', 'foo'], optional=True)
            assert isinstance(rv, Response)
            assert rv.json == {'x': 1, 'status': 200}

    # Test: if we pass a text then it must return it as is.
    def test_handler_text_no_quotes(self, app):
        with req(app, '/?callback=foo'):
            r = _json_p_handler(str('hello'),
                                callbacks=['callback'], optional=False,
                                add_quotes=False)
            assert r.get_data(as_text=True) == 'foo(hello);'
            assert r.status_code == 200
            assert r.headers['Content-Type'] == 'application/javascript'
            # For py 2.x we also test unicode string.
            if sys.version_info[0] == 2:
                r = _json_p_handler(unicode('hello'),
                                    callbacks=['callback'], optional=False,
                                    add_quotes=False)
                assert r.get_data(as_text=True) == 'foo(hello);'

    # Test: if we pass a text then it must return quoted string.
    def test_handler_text_quotes(self, app):
        with req(app, '/?callback=foo'):
            r = _json_p_handler(str('hello'), optional=False, add_quotes=True)
            assert r.get_data(as_text=True) == 'foo("hello");'
            assert r.status_code == 200
            assert r.headers['Content-Type'] == 'application/javascript'
            # For py 2.x we also test unicode string.
            if sys.version_info[0] == 2:
                r = _json_p_handler(unicode('hello'),
                                    callbacks=['callback'], optional=False,
                                    add_quotes=True)
                assert r.get_data(as_text=True) == 'foo("hello");'

    # Test: text with quotes.
    def test_handler_text_quotes2(self, app):
        with req(app, '/?callback=foo'):
            r = _json_p_handler(str('hello "Sam"'), add_quotes=True)
            assert r.get_data(as_text=True) == r'foo("hello \"Sam\"");'
            assert r.status_code == 200
            assert r.headers['Content-Type'] == 'application/javascript'

    # Test: same as above but used configuration instead of kwarg,
    # it adds quotes by default.
    def test_handler_text_default(self, app):
        with req(app, '/?callback=foo'):
            r = _json_p_handler(str('hello'))
            assert r.get_data(as_text=True) == 'foo("hello");'
            assert r.status_code == 200
            assert r.headers['Content-Type'] == 'application/javascript'
            # For py 2.x we also test unicode string.
            if sys.version_info[0] == 2:
                r = _json_p_handler(unicode('hello'), callbacks=['callback'],
                                    optional=False)
                assert r.get_data(as_text=True) == 'foo("hello");'

    # Test: pass json response.
    def test_handler_json(self, app):
        with req(app, '/?callback=foo'):
            r = json_response(val=100, add_status_=False)
            val = _json_p_handler(r, callbacks=['callback'], optional=False)

            res = val.get_data(as_text=True).replace(' ', '').replace('\n', '')
            assert res == 'foo({"val":100});'

            assert val.status_code == 200
            assert val.headers['Content-Type'] == 'application/javascript'

    # Test: simple usage, no callback; it must proceed like @as_json.
    def test_simple_no_jsonp(self, app):
        @as_json_p
        def view():
            return dict(val=1, name='Sam')

        with req(app, '/'):
            r = view()
            assert r.status_code == 200
            assert r.headers['Content-Type'] == 'application/json'
            assert r.json == {'val': 1, 'name': 'Sam', 'status': 200}

    # Test: simple usage, with callback.
    def test_simple(self, app):
        @as_json_p
        def view():
            return dict(val=1, name='Sam')

        with req(app, '/?callback=foo'):
            r = view()
            assert r.status_code == 200
            assert r.headers['Content-Type'] == 'application/javascript'
            # Build test value.
            param = json.jsonify(val=1, name='Sam').get_data(as_text=True)
            if param.endswith('\n'):
                param = param[:-1]
            text = 'foo(%s);' % param
            assert r.get_data(as_text=True) == text

    # Test: simple usage, with alternate callback.
    # By default callback name may be 'callback' or 'jsonp'.
    def test_simple2(self, app):
        @as_json_p
        def view():
            return dict(val=1, name='Sam')

        with req(app, '/?jsonp=foo'):
            r = view()
            assert r.status_code == 200
            assert r.headers['Content-Type'] == 'application/javascript'

            param = json.jsonify(val=1, name='Sam').get_data(as_text=True)
            # In flask 0.11 it adds '\n' to the end, we don't need it here.
            if param.endswith('\n'):
                param = param[:-1]
            text = 'foo(%s);' % param
            assert r.get_data(as_text=True) == text

    # Test: @as_json_p with parameters, with missing callback.
    # Here we force @as_json_p to use custom callback names
    # and make it required.
    def test_complex_required_missing(self, app):
        @as_json_p(callbacks=['boo'], optional=False)
        def view():
            return dict(val=1, name='Sam')

        with req(app, '/?callback=foo'):
            with pytest.raises(BadRequest):
                view()

    # Test: @as_json_p with parameters.
    # Here we force @as_json_p to use custom callback names
    # and make it required.
    def test_complex_required(self, app):
        @as_json_p(callbacks=['boo'], optional=False)
        def view():
            return dict(val=1, name='Sam')

        with req(app, '/?boo=foo'):
            r = view()
            assert r.status_code == 200
            assert r.headers['Content-Type'] == 'application/javascript'

            param = json.jsonify(val=1, name='Sam').get_data(as_text=True)
            # In flask 0.11 it adds '\n' to the end, we don't need it here.
            if param.endswith('\n'):
                param = param[:-1]
            text = 'foo(%s);' % param
            assert r.get_data(as_text=True) == text

    # Test: simple usage, no callback; it must proceed like @as_json.
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_simple_no_jsonp_int(self, app):
        @as_json_p
        def view():
            return 1

        with req(app, '/'):
            r = view()
            assert r.status_code == 200
            assert r.headers['Content-Type'] == 'application/json'
            assert r.json == 1

    # Test: return integer.
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_simple_int(self, app):
        @as_json_p
        def view():
            return 1

        with req(app, '/?callback=foo'):
            r = view()
            assert r.status_code == 200
            assert r.headers['Content-Type'] == 'application/javascript'
            assert r.get_data(as_text=True) == 'foo(1);'

    # Test: return string.
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_simple_str(self, app):
        @as_json_p
        def view():
            return '12\"3'

        with req(app, '/?callback=foo'):
            r = view()
            assert r.status_code == 200
            assert r.headers['Content-Type'] == 'application/javascript'
            assert r.get_data(as_text=True) == 'foo("12\\"3");'

    # Test: return array.
    @pytest.mark.skipif(pytest.flask_ver < (0, 11),
                        reason="requires flask >= 0.11")
    def test_simple_array(self, app):
        @as_json_p
        def view():
            return ['1', 2]

        with req(app, '/?callback=foo'):
            r = view()
            assert r.status_code == 200
            assert r.headers['Content-Type'] == 'application/javascript'
            param = json.jsonify(['1', 2]).get_data(as_text=True)
            if param.endswith('\n'):
                param = param[:-1]
            text = 'foo(%s);' % param
            assert r.get_data(as_text=True) == text
