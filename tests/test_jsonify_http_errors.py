"""
This module provides tests for JSON_JSONIFY_HTTP_ERRORS feature.
"""
from flask import abort
from flask_json import FlaskJSON
import pytest
from werkzeug.exceptions import InternalServerError, NotFound


@pytest.fixture
def theapp(app):
    # Enable feature
    app.config['JSON_JSONIFY_HTTP_ERRORS'] = True
    # set raise to result in 500 error
    app.config["PROPAGATE_EXCEPTIONS"] = False
    FlaskJSON(app)
    return app


class TestJsonifyHttpError(object):
    # Test: raise HTTP error by flask.abort
    def test_abort(self, theapp, client):
        @theapp.route('/test')
        def endpoint():
            abort(404)

        r = client.get('/test')
        assert r.status_code == 404
        assert r.json == {
            'status': 404,
            'description': NotFound.description,
            'reason': 'Not Found',
        }

    # Test: don't add status code to the response.
    def test_no_status(self, theapp, client):
        @theapp.route('/test')
        def endpoint():
            abort(404)
        theapp.config["JSON_ADD_STATUS"] = False

        r = client.get('/test')
        assert r.status_code == 404
        assert r.json == {
            'description': NotFound.description,
            'reason': 'Not Found',
        }

    # Test: raise an HTTP exception without the description.
    def test_no_description(self, theapp, client):
        @theapp.route('/test')
        def endpoint():
            raise NotFound(description='')

        r = client.get('/test')
        assert r.status_code == 404
        assert r.json == {
            'status': 404,
            # NOTE: default description is used.
            'description': NotFound.description,
            'reason': 'Not Found',
        }

    # Test: raise HTTP error by flask.abort with custom message
    def test_abort_with_custom_message(self, theapp, client):
        @theapp.route('/test')
        def endpoint():
            abort(400, 'Custom message')

        r = client.get('/test')
        assert r.status_code == 400
        assert r.json == {
            'status': 400,
            'description': 'Custom message',
            'reason': 'Bad Request',
        }

    # Test: raise regular Exception
    def test_raise_exception(self, theapp, client):
        @theapp.route('/test')
        def endpoint():
            raise ValueError()

        r = client.get('/test')
        assert r.status_code == 500
        assert r.json == {
            'status': 500,
            'description': InternalServerError.description,
            'reason': 'Internal Server Error',
        }
