"""
This module provides Flask-JSON initialization test.
"""
from .common import *
from flask_json import FlaskJSON, JSONEncoderEx, JsonRequest, JsonTestResponse


# Test: initial state on create.
def test_create():
    ext = FlaskJSON()
    assert_is_none(ext._app)
    assert_is_none(ext._error_handler_func)
    assert_is_none(ext._decoder_error_func)
    assert_is(ext._encoder_class, JSONEncoderEx)


# Test: initial config on init with constructor.
def test_init_constructor():
    app = Flask(__name__)
    ext = FlaskJSON(app)

    assert_equals(app.config.get('JSON_ADD_STATUS'), True)
    assert_is_none(app.config.get('JSON_DATE_FORMAT'))
    assert_is_none(app.config.get('JSON_TIME_FORMAT'))
    assert_is_none(app.config.get('JSON_DATETIME_FORMAT'))
    assert_equals(app.config.get('JSON_DECODE_ERROR_MESSAGE'), 'Not a JSON.')
    assert_is(app.request_class, JsonRequest)
    assert_is(app.json_encoder, JSONEncoderEx)
    assert_equals(app.extensions['json'], ext)


# Test: initial config on deferred init.
def test_init_deferred():
    app = Flask(__name__)

    # Check if we correctly handle this.
    # Well actually it's to increase test coverage.
    del app.extensions

    ext = FlaskJSON()
    ext.init_app(app)

    assert_equals(app.config.get('JSON_ADD_STATUS'), True)
    assert_is_none(app.config.get('JSON_DATE_FORMAT'))
    assert_is_none(app.config.get('JSON_TIME_FORMAT'))
    assert_is_none(app.config.get('JSON_DATETIME_FORMAT'))
    assert_equals(app.config.get('JSON_DECODE_ERROR_MESSAGE'), 'Not a JSON.')
    assert_is(app.request_class, JsonRequest)
    # No testing response class on production.
    assert_is_not(app.response_class, JsonTestResponse)
    assert_is(app.json_encoder, JSONEncoderEx)
    assert_equals(app.extensions['json'], ext)


# Test: JsonTestResponse is set for testing mode.
def test_init_testmode():
    app = Flask(__name__)
    app.config['TESTING'] = True
    FlaskJSON(app)
    assert_is(app.response_class, JsonTestResponse)


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

    assert_equals(ext._error_handler_func, err_handler_func)
    assert_equals(ext._decoder_error_func, decoder_func)

    # If FlaskJSON is not initialized with the app then only
    # '_encoder_class' will be set.
    assert_is_not_none(ext._encoder_class)
    assert_is_not(app.json_encoder, ext._encoder_class)

    # And after initialization we set our json encoder.
    ext.init_app(app)
    assert_is(app.json_encoder, ext._encoder_class)


# Test: decorators for initialized extension.
def test_decorators_initialized():
    app = Flask(__name__)
    ext = FlaskJSON(app)

    @ext.invalid_json_error
    def decoder_func():
        pass

    # If we apply decorator on initialized extension then it sets
    # encoder class immediately.
    assert_is(app.json_encoder, ext._encoder_class)
