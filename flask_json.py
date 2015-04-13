"""
    flask_json
    ----------

    A Flask extension providing better JSON support.

    :copyright: (c) 2015 by Sergey Kozlov
    :license: BSD, see LICENSE for more details.
"""
import sys
from datetime import datetime, date, time
from speaklater import _LazyString
from flask import current_app, jsonify, Request
from flask.json import JSONEncoder
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

__version__ = '0.0.1'

text_type = unicode if sys.version_info[0] == 2 else str


def json_response(status=200, **kwargs):
    """Function to build JSON response with the given HTTP status.

    It also puts status to the JSON as ``status`` field if
    ``JSON_ADD_STATUS`` is True.

    Args:
        status: HTTP response status code
        kwargs: keyword arguments to put in result JSON.

    Returns:
        :class:`flask.Response` with the JSON content.

    See Also:
            :func:`flask.json.jsonify` and :class:`JsonErrorResponse`.
    """
    if current_app.config['JSON_ADD_STATUS']:
        kwargs['status'] = status
    response = jsonify(**kwargs)
    response.status_code = status
    return response


# TODO: maybe subclass from HTTPException?
class JsonErrorResponse(Exception):
    """Exception which will be converted to JSON response.

    Usage::

        raise JsonErrorResponse(description='text')
        raise JsonErrorResponse(status=401, one='text', two=12)
    """
    def __init__(self, status=400, **kwargs):
        """Construct JSON exception.

        Args:
            status: HTTP response status code.
            kwargs: keyword arguments to put in result JSON.

        See Also:
            :func:`.core.json_response`.
        """
        assert status != 200
        super(JsonErrorResponse, self).__init__()
        self.status = status
        self.data = kwargs


class JsonRequest(Request):
    """This class changes :class:`flask.Request` behaviour on JSON parse error.

    If HTTP response doesn't contain JSON data and you call
    :samp:`request.get_json()` then :class:`JsonErrorResponse` will be raised.

    See Also:
        ``JSON_DECODE_ERROR_MESSAGE`` configuration
        and :meth:`FlaskJSON.decoder_error`.
    """
    def on_json_loading_failed(self, e):
        """
        Raises:
            JsonErrorResponse: Not a JSON.
        """
        # Try decoder error hook firstly; see FlaskJSON.decoder_error().
        func = current_app.extensions['json']._decoder_error_func
        if func is not None:
            return func(e)

        # By defualt we raise json error with description.
        # If there is no description config or it's text is empty then
        # raise without a description.
        else:
            desc = current_app.config.get('JSON_DECODE_ERROR_MESSAGE')
            if desc:
                raise JsonErrorResponse(description=desc)
            else:
                raise JsonErrorResponse()


class JSONEncoderEx(JSONEncoder):
    """Extends default Flask JSON encoder with more types:
    date, time and bablel strings. Also overrides datetime encoding.

    Datetime, date and time will be converted to ISO 8601 format by default.

    See Also:
        ``JSON_DATETIME_FORMAT``, ``JSON_DATE_FORMAT`` and ``JSON_TIME_FORMAT``
        configurations.
    """
    def default(self, o):
        if isinstance(o, _LazyString):
            return text_type(o)
        elif isinstance(o, datetime):
            fmt = current_app.config.get('JSON_DATETIME_FORMAT')
            return o.isoformat() if fmt is None else o.strftime(fmt)
        elif isinstance(o, date):
            fmt = current_app.config.get('JSON_DATE_FORMAT')
            return o.isoformat() if fmt is None else o.strftime(fmt)
        elif isinstance(o, time):
            fmt = current_app.config.get('JSON_TIME_FORMAT')
            return o.isoformat() if fmt is None else o.strftime(fmt)
        return JSONEncoder.default(self, o)


class FlaskJSON(object):
    """Flask-JSON extension class."""
    def __init__(self, app=None):
        self._app = app
        self._error_handler_func = None
        self._decoder_error_func = None
        self._encoder_class = JSONEncoderEx
        if app is not None:
            self.init_app(app)

    def _error_handler(self, e):
        if self._error_handler_func is not None:
            return self._error_handler_func(e)
        return json_response(e.status, **e.data)

    def init_app(self, app):
        """Initializes the application with the extension.

        Args:
            app: Flask application object.
        """
        app.config.setdefault('JSON_ADD_STATUS', True)
        app.config.setdefault('JSON_DECODE_ERROR_MESSAGE', 'Not a JSON.')

        if not hasattr(app, 'extensions'):
            app.extensions = dict()
        app.extensions['json'] = self

        self._app = app
        app.request_class = JsonRequest
        app.json_encoder = self._encoder_class
        app.errorhandler(JsonErrorResponse)(self._error_handler)

    def error_handler(self, func):
        """This decorator allows to set cusotom handler for the
        :class:`JsonErrorResponse` exception.

        By default JSON response will be generated with HTTP 400.

        See Also:
            :func:`json_response`.
        """
        self._error_handler_func = func
        return func

    def encoder(self, func):
        """This decorator allows to add extra
        """
        class JSONEncoderWithHook(JSONEncoderEx):
            def default(self, o):
                result = func(o)
                if result is not None:
                    return result
                return JSONEncoderEx.default(self, o)
        if self._app is not None:
            self._app.json_encoder = JSONEncoderWithHook
        else:
            self._encoder_class = JSONEncoderWithHook
        return func

    def decoder_error(self, func):
        self._decoder_error_func = func
        return func
