"""
This module provides Flask-JSON initialization test.
"""
from flask import Flask
from flask_json import FlaskJSON, JSONEncoderEx, JsonRequest, JsonTestResponse


# Test: initial state on create.
def test_create():
    ext = FlaskJSON()
    assert ext._app is None
    assert ext._error_handler_func is None
    assert ext._decoder_error_func is None
    assert ext._encoder_class is JSONEncoderEx


# Test: initial config on init with constructor.
def test_init_constructor():
    app = Flask(__name__)
    ext = FlaskJSON(app)

    app.config.get('JSON_ADD_STATUS') == True
    assert app.config.get('JSON_DATE_FORMAT') is None
    assert app.config.get('JSON_TIME_FORMAT') is None
    assert app.config.get('JSON_DATETIME_FORMAT') is None
    assert app.config.get('JSON_DECODE_ERROR_MESSAGE') == 'Not a JSON.'
    assert app.request_class is JsonRequest
    assert app.json_encoder is JSONEncoderEx
    assert app.extensions['json'] == ext


# Test: initial config on deferred init.
def test_init_deferred():
    app = Flask(__name__)

    # Check if we correctly handle this.
    # Well actually it's to increase test coverage.
    del app.extensions

    ext = FlaskJSON()
    ext.init_app(app)

    assert app.config.get('JSON_ADD_STATUS') == True
    assert app.config.get('JSON_DATE_FORMAT') is None
    assert app.config.get('JSON_TIME_FORMAT') is None
    assert app.config.get('JSON_DATETIME_FORMAT') is None
    assert app.config.get('JSON_DECODE_ERROR_MESSAGE') == 'Not a JSON.'
    assert app.request_class is JsonRequest
    # No testing response class on production.
    assert app.response_class is not JsonTestResponse
    assert app.json_encoder is JSONEncoderEx
    assert app.extensions['json'] == ext


# Test: JsonTestResponse is set for testing mode.
def test_init_testmode():
    app = Flask(__name__)
    app.config['TESTING'] = True
    FlaskJSON(app)
    assert app.response_class is JsonTestResponse


# Test: decorators for uninitialized extension.
def test_decorators():
    app = Flask(__name__)
    ext = FlaskJSON()

    @ext.error_handler
    def err_handler_func():
        pass

    @ext.invalid_json_error
    def decoder_func():
        pass

    @ext.encoder
    def encoder_func():
        pass

    assert ext._error_handler_func == err_handler_func
    assert ext._decoder_error_func == decoder_func

    # If FlaskJSON is not initialized with the app then only
    # '_encoder_class' will be set.
    assert ext._encoder_class is not None
    assert app.json_encoder is not ext._encoder_class

    # And after initialization we set our json encoder.
    ext.init_app(app)
    assert app.json_encoder is ext._encoder_class


# Test: decorators for initialized extension.
def test_decorators_initialized():
    app = Flask(__name__)
    ext = FlaskJSON(app)

    @ext.invalid_json_error
    def decoder_func():
        pass

    # If we apply decorator on initialized extension then it sets
    # encoder class immediately.
    assert app.json_encoder is ext._encoder_class
