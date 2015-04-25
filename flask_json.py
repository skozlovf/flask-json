"""
    flask_json
    ~~~~~~~~~~

    A Flask extension providing better JSON support.

    :copyright: (c) 2015 by Sergey Kozlov
    :license: BSD, see LICENSE for more details.
"""
import sys
import collections
from datetime import datetime, date, time
try:
    from speaklater import _LazyString
# Don't cover since simulated in test_encoder_nospeaklater().
except ImportError:  # pragma: no cover
    _LazyString = None
from flask import current_app, jsonify, Request
from flask import json

__version__ = '0.0.1'

text_type = unicode if sys.version_info[0] == 2 else str


def json_response(status_=200, headers_=None, **kwargs):
    """Helper function to build JSON response
    with the given HTTP status and fields(``kwargs``).

    It also puts HTTP status code to the JSON response if
    :ref:`JSON_ADD_STATUS <opt_add_status>` is ``True``::

        app.config['JSON_ADD_STATUS'] = True
        json_response(test=12)
        # {"status": 200, "test": 12}, response HTTP status is 200.

        json_response(400, test=12)
        # {"status": 400, "test": 12}, response HTTP status is 400.

        json_response(status_=401, test=12)
        # {"status": 401, "test": 12}, response HTTP status is 401.

        app.config['JSON_ADD_STATUS'] = False
        json_response(test=12)
        # {"test": 12}, response HTTP status is 200.

    Name of the HTTP status filed is configurable and can be changed with
    :ref:`JSON_STATUS_FIELD_NAME <opt_status_name>`::

        app.config['JSON_ADD_STATUS'] = True
        app.config['JSON_STATUS_FIELD_NAME'] = 'http_status'
        json_response(test=12)
        # {"http_status": 200, "test": 12}, response HTTP status is 200.

    If ``kwargs`` already contains key with the same name as
    ``JSON_STATUS_FIELD_NAME`` then it's value will be used instead of HTTP
    status code::

        app.config['JSON_ADD_STATUS'] = True

        json_response(status_=400, status=100500, test=12)
        # {"status": 100500, "test": 12}, but response HTTP status is 400.

        json_response(status=100500, test=12)
        # {"status": 100500, "test": 12}, but response HTTP status is 200.

        app.config['JSON_STATUS_FIELD_NAME'] = 'http_status'
        json_response(http_status=100500, test=12)
        # {"http_status": 100500, "test": 12}, but response HTTP status is 200.

    You also may add custom headers to the JSON response by passing iterable or
    dict to `headers_`::

        # One way.
        headers = {'MY-HEADER': value, 'X-EXTRA': 123}
        json_response(headers_=headers, test=12)

        # Another way (tuple, list, iterable).
        headers = (('MY-HEADER', value), ('X-EXTRA', 123))
        json_response(headers_=headers, test=12)

    Args:
        `status_`: HTTP response status code.
        `headers_`: iterable or dictionary with header values.
        kwargs: keyword arguments to put in result JSON.

    Returns:
        flask.Response: Response with the JSON content.
    """
    if current_app.config['JSON_ADD_STATUS']:
        field = current_app.config['JSON_STATUS_FIELD_NAME']
        if field not in kwargs:
            kwargs[field] = status_
    response = jsonify(**kwargs)
    response.status_code = status_

    if headers_ is not None:
        response.headers.extend(headers_)

    return response


# TODO: maybe subclass from HTTPException?
class JsonErrorResponse(Exception):
    """Exception which will be converted to JSON response.

    Usage::

        raise JsonErrorResponse(description='text')
        raise JsonErrorResponse(status=401, one='text', two=12)

    Args:
        status: HTTP response status code.
        kwargs: keyword arguments to put in result JSON.

    See Also:
        :func:`.json_response`,
        :meth:`@error_handler <.FlaskJSON.error_handler>`.
    """
    def __init__(self, status=400, **kwargs):
        super(JsonErrorResponse, self).__init__()
        assert status != 200
        self.status = status
        self.data = kwargs


class JsonRequest(Request):
    """This class changes :class:`flask.Request` behaviour on JSON parse errors.

    :meth:`flask.Request.get_json` will raise :class:`.JsonErrorResponse`
    by default on invalid JSON content.

    See Also:
        :ref:`JSON_DECODE_ERROR_MESSAGE <opt_decode_error_msg>`,
        :meth:`@invalid_json_error <.FlaskJSON.invalid_json_error>`
    """
    def on_json_loading_failed(self, e):
        # Try decoder error hook firstly; see FlaskJSON.invalid_json_error().
        func = current_app.extensions['json']._decoder_error_func
        if func is not None:
            response = func(e)
            if response is not None:
                return response

        # By default we raise json error with description.
        # If there is no description config or it's text is empty then
        # raise without a description.
        desc = current_app.config.get('JSON_DECODE_ERROR_MESSAGE')
        if desc:
            raise JsonErrorResponse(description=desc)
        else:
            raise JsonErrorResponse()


class JSONEncoderEx(json.JSONEncoder):
    """Extends default Flask JSON encoder with more types:

    * iterable;
    * :class:`~datetime.datetime`;
    * :class:`~datetime.date`;
    * :class:`~datetime.time`;
    * `speaklater <https://pypi.python.org/pypi/speaklater>`_ lazy strings;
    * objects with ``__json__()`` or ``for_json()`` methods.

    Time related values will be converted to ISO 8601 format by default.

    See Also:
        :ref:`JSON_DATETIME_FORMAT <opt_fmt_datetime>`,
        :ref:`JSON_DATE_FORMAT <opt_fmt_date>`,
        :ref:`JSON_TIME_FORMAT <opt_fmt_time>`,
        :ref:`JSON_USE_ENCODE_METHODS <opt_use_enc_methods>`.
    """
    def default(self, o):
        # We have to test _LazyString before Iterable to prevent
        # converting string to list of chars, since string is iterable too.
        if _LazyString is not None and isinstance(o, _LazyString):
            return text_type(o)
        elif isinstance(o, collections.Iterable):
            # All iterables will be converted to list.
            return list(o)
        elif isinstance(o, datetime):
            fmt = current_app.config.get('JSON_DATETIME_FORMAT')
            return o.strftime(fmt) if fmt else o.isoformat()
        elif isinstance(o, date):
            fmt = current_app.config.get('JSON_DATE_FORMAT')
            return o.strftime(fmt) if fmt else o.isoformat()
        elif isinstance(o, time):
            fmt = current_app.config.get('JSON_TIME_FORMAT')
            return o.strftime(fmt) if fmt else o.isoformat()
        elif current_app.config.get('JSON_USE_ENCODE_METHODS'):
            if hasattr(o, '__json__'):
                return o.__json__()
            elif hasattr(o, 'for_json'):
                return o.for_json()
        return super(JSONEncoderEx, self).default(o)


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
        app.config.setdefault('JSON_STATUS_FIELD_NAME', 'status')
        app.config.setdefault('JSON_DECODE_ERROR_MESSAGE', 'Not a JSON.')

        if not hasattr(app, 'extensions'):
            app.extensions = dict()
        app.extensions['json'] = self

        self._app = app
        app.request_class = JsonRequest
        app.json_encoder = self._encoder_class
        app.errorhandler(JsonErrorResponse)(self._error_handler)

    def error_handler(self, func):
        """This decorator allows to set custom handler for the
        :class:`.JsonErrorResponse` exceptions.

        In custom handler you may return :class:`flask.Response` or raise
        an exception. If user defined handler returns ``None`` then default
        action takes place (generate JSON response from the exception).

        Example:

            ::

                json = FlaskJson(app)
                ...

                @json.error_handler
                def custom_error_handler(e):
                    # e is JsonErrorResponse.
                    return json_response(status=401)

        See Also:
            :meth:`.invalid_json_error`.
        """
        self._error_handler_func = func
        return func

    def invalid_json_error(self, func):
        """This decorator allows to set custom handler for the invalid
        JSON requests.

        It will be called by the
        :meth:`request.get_json() <flask.Request.get_json>`.

        If the handler returns or raises nothing then Flask-JSON
        raises :class:`.JsonErrorResponse`.

        Example:

            ::

                json = FlaskJson(app)
                ...

                @json.invalid_json_error
                def invalid_json_error(e):
                    raise SomeException

        By default JSON response will be generated with HTTP 400::

            {"status": 400, "description": "Not a JSON."}

        You also may return a value from the handler then it will be used as
        :meth:`request.get_json() <flask.Request.get_json>` result on errors.

        See Also:
            :ref:`JSON_DECODE_ERROR_MESSAGE <opt_decode_error_msg>`
        """
        self._decoder_error_func = func
        return func

    def encoder(self, func):
        """This decorator allows to set extra JSON encoding step on response
        building.

        JSON encoding order:

        * User defined encoding.
        * Flask-JSON encoding.
        * Flask encoding.

        If user defined encoder returns None then default encoders takes place
        (Flask-JSON and then Flask).

        Example:

            ::

                json = FlaskJson(app)
                ...

                @json.encoder
                def custom_encoder(o):
                    if isinstance(o, MyClass):
                        return o.to_string()
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
