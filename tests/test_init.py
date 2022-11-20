"""
This module provides Flask-JSON initialization test.
"""
from flask import Flask
from flask.json.provider import DefaultJSONProvider
from flask_json import FlaskJSON, FlaskJSONProvider, FlaskJSONRequest, _encoder


# Test: initial state on create.
def test_create():
    ext = FlaskJSON()
    assert ext._error_handler_func is None
    assert ext._decoder_error_func is None
    assert ext._encoders == [_encoder, DefaultJSONProvider.default]


# Test: initial config on init with constructor.
def test_init_constructor():
    app = Flask('testapp')
    ext = FlaskJSON(app)

    assert app.config.get('JSON_ADD_STATUS') is True
    assert app.config.get('JSON_DATE_FORMAT') is None
    assert app.config.get('JSON_TIME_FORMAT') is None
    assert app.config.get('JSON_DATETIME_FORMAT') is None
    assert app.config.get('JSON_DECODE_ERROR_MESSAGE') == 'Not a JSON.'
    assert app.request_class is FlaskJSONRequest
    assert app.json_provider_class is FlaskJSONProvider
    assert isinstance(app.json, FlaskJSONProvider)
    assert app.extensions['json'] is ext


# Test: initial config on deferred init.
def test_init_deferred():
    app = Flask('testapp')

    ext = FlaskJSON()
    ext.init_app(app)

    assert app.config.get('JSON_ADD_STATUS') is True
    assert app.config.get('JSON_DATE_FORMAT') is None
    assert app.config.get('JSON_TIME_FORMAT') is None
    assert app.config.get('JSON_DATETIME_FORMAT') is None
    assert app.config.get('JSON_DECODE_ERROR_MESSAGE') == 'Not a JSON.'
    assert app.request_class is FlaskJSONRequest
    assert app.json_provider_class is FlaskJSONProvider
    assert isinstance(app.json, FlaskJSONProvider)
    # No testing response class on production.
    # assert app.response_class is not JsonTestResponse
    assert app.extensions['json'] is ext


# Test: FlaskJSON.error_handler() decorator.
def test_error_handler_deco():
    ext = FlaskJSON()

    @ext.error_handler
    def err_handler_func():
        pass

    assert ext._error_handler_func is err_handler_func


# Test: FlaskJSON.invalid_json_error() decorator.
def test_invalid_json_error_deco():
    ext = FlaskJSON()

    @ext.invalid_json_error
    def decoder_func():
        pass

    assert ext._decoder_error_func is decoder_func


# Test: FlaskJSON.encoder() decorator.
def test_encoder_deco():
    ext = FlaskJSON()

    @ext.encoder
    def func():
        pass

    assert ext._encoders == [func, _encoder, DefaultJSONProvider.default]


# Test: FlaskJSON.encoder() decorator, multiple calls.
def test_encoder_multi_deco():
    ext = FlaskJSON()

    @ext.encoder
    def func1():
        pass

    @ext.encoder
    def func2():
        pass

    assert ext._encoders == [func2, func1, _encoder, DefaultJSONProvider.default]
