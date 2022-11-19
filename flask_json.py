"""
    flask_json
    ~~~~~~~~~~

    A Flask extension providing better JSON support.

    :copyright: (c) 2015 - 2017 by Sergey Kozlov
    :license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import
import sys
try:
    import collections.abc as collections_abc  # python 3.3+
except ImportError:
    import collections as collections_abc
from functools import partial, wraps
from datetime import datetime, date, time
try:
    from speaklater import _LazyString
# Don't cover since simulated in test_encoder_nospeaklater().
except ImportError:  # pragma: no cover
    _LazyString = None
from werkzeug.exceptions import default_exceptions, BadRequest, HTTPException
from flask import current_app, jsonify, request, Request, Response
from flask import json

__version__ = '0.3.5'


if sys.version_info[0] == 2:
    text_type = unicode

    def _is_str(value):
        return isinstance(value, str) or isinstance(value, unicode)
else:
    text_type = str

    def _is_str(value):
        return isinstance(value, str)


def json_response(status_=200, headers_=None, add_status_=None, data_=None,
                  **kwargs):
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
        `add_status_`: Add status field. If not set then
            :ref:`JSON_ADD_STATUS <opt_add_status>` is used.
        `data_`: Data to put in result JSON. It can be used instead of
            ``kwargs`` or if you want to pass non-dictionary value.
        `kwargs`: keyword arguments to put in result JSON.

    Returns:
        flask.Response: Response with the JSON content.

    Note:
        Only ``data_`` or ``kwargs`` is allowed.

        If ``data_`` is not a :class:`dict` then ``add_status_`` and
        :ref:`JSON_ADD_STATUS <opt_add_status>` are ignored and no status
        is stored in the result JSON.

        If :class:`dict` is passed via ``data_`` then behaviour is like you
        pass data in the keyword arguments.

    .. versionchanged:: 0.3.2
       Added ``data_`` and non-dictionary values support.
    """
    assert data_ is None or not kwargs

    if isinstance(data_, dict):
        kwargs = data_
        data_ = None

    if data_ is not None:
        add_status = False
    elif add_status_ is not None:
        add_status = add_status_
    else:
        add_status = current_app.config['JSON_ADD_STATUS']

    if add_status:
        field = current_app.config['JSON_STATUS_FIELD_NAME']
        if field not in kwargs:
            kwargs[field] = status_

    if data_ is None and not kwargs:
        data_ = {}

    response = jsonify(data_) if data_ is not None else jsonify(**kwargs)
    response.status_code = status_

    if headers_ is not None:
        response.headers.extend(headers_)

    return response


# Helper function to normalize view return values for @as_json decorator.
# It always returns (dict, status, headers). Missing values will be None.
# For example in such cases when tuple_ is
#   (dict, status), (dict, headers), (dict, status, headers),
#   (dict, headers, status)
#
# It assumes what status is int, so this construction will not work:
# (dict, None, headers) - it doesn't make sense because you just use
# (dict, headers) if you want to skip status.
def _normalize_view_tuple(tuple_):
    v = tuple_ + (None,) * (3 - len(tuple_))
    return v if isinstance(v[1], int) else (v[0], v[2], v[1])


# Helper function to create JSON response for the given data.
# Raises an error if the data is not convertible to JSON.
def _build_response(data, add_status=None):
    if data is None:
        return json_response(add_status_=add_status)
    elif isinstance(data, dict):
        return json_response(add_status_=add_status, **data)
    elif isinstance(data, Response):
        assert 'application/json' in data.mimetype
        return data
    elif isinstance(data, tuple):
        d, status, headers = _normalize_view_tuple(data)
        if isinstance(d, dict):
            return json_response(status_=status or 200, headers_=headers,
                                 add_status_=add_status, **d)
        else:
            return json_response(status_=status or 200, headers_=headers,
                                 add_status_=add_status, data_=d)
    else:
        return json_response(data_=data)
        # raise ValueError('Unsupported return value.')


def as_json(f):
    """This decorator converts view's return value to JSON response.

    The decorator expects the following return values:
        * Flask :class:`~flask.Response` instance (see note bellow);
        * a ``dict`` with JSON content;
        * a tuple of ``(dict, status)`` or ``(dict, headers)`` or
          ``(dict, status, headers)`` or ``(dict, headers, status)``.

    Instead of ``dict`` you may pass ``None`` and it will be treated as empty
    JSON (same as ``dict()`` or ``{}``).

    In all other cases it raises an error.

    The decorator provides the same features as :func:`.json_response`.

    Usage::

        @as_json
        def view_simple():
            return dict(param=value, param2=value2)

        @as_json
        def view_simple2():
            return [1, 2, 3]

        @as_json
        def view_comp():
            return dict(param=value, param2=value2), 400

    Note:
        If wrapped view returns Flask :class:`~flask.Response` then it will be
        used as is without passing to :func:`.json_response`. But the response
        must be a JSON response (mimetype must contain ``application/json``),
        otherwise ``AssertionError`` will be raised.

    Returns:
        flask.Response: Response with the JSON content.

    Raises:
        ValueError: if return value is not supported.

    See Also:
        :func:`.json_response`
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        rv = f(*args, **kwargs)
        return _build_response(rv)

    return wrapper


# Helper function to handle JSONP response.
# Used in the @as_json_p decorator.
def _json_p_handler(rv, callbacks=None, optional=None, add_quotes=None):
    callbacks = callbacks or current_app.config['JSON_JSONP_QUERY_CALLBACKS']
    if optional is None:
        optional = current_app.config['JSON_JSONP_OPTIONAL']
    if add_quotes is None:
        add_quotes = current_app.config['JSON_JSONP_STRING_QUOTES']

    callback = None
    for k in callbacks:
        if k in request.args:
            callback = request.args.get(k)
            break

    if callback is None:
        if optional:
            return _build_response(rv)
        else:
            raise BadRequest('Missing JSONP callback parameter.')

    # NOTE: flask 0.11 adds '\n' to the end but we don't need it here.

    if _is_str(rv):
        if rv.endswith('\n'):  # pragma: no cover
            rv = rv[:-1]
        if add_quotes:
            data = '"%s"' % rv.replace('"', '\\"')
        else:
            data = '%s' % rv
    else:
        data = _build_response(rv, add_status=False).get_data(as_text=True)
        if data.endswith('\n'):  # pragma: no cover
            data = data[:-1]

    data = text_type('%s(%s);') % (callback, data)
    response = current_app.response_class(
        data, status=200, content_type='application/javascript')
    return response


def as_json_p(f=None, callbacks=None, optional=None, add_quotes=None):
    """This decorator acts like :func:`@as_json <flask_json.as_json>` but
    also handles JSONP requests; expects string or any
    :func:`@as_json <flask_json.as_json>` supported return value.

    It may be used in two forms:

    * Without parameters - then global configuration will be applied::

          @as_json_p
          def view():
              ...

    * With parameters - then they will have priority over global ones for the
      given view::

          @as_json_p(...)
          def view():
              ...

    Strings may be surrounded with quotes depending on configuration
    (``add_quotes`` or :ref:`JSON_JSONP_STRING_QUOTES <opt_jsonp_quotes>`)::

        ...
        @as_json_p
        def view():
            return 'str'

        app.config['JSON_JSONP_STRING_QUOTES'] = False
        # view() ->  callback(str);

        app.config['JSON_JSONP_STRING_QUOTES'] = True
        # view() ->  callback("str");

    Note:
        If view returns custom headers or HTTP status then
        they will be discarded.
        Also HTTP status field will not be passed to the callback.

    Args:
        callbacks: List of acceptable callback query parameters.
        optional: Make JSONP optional. If no callback is passed then fallback
            to JSON response.
        add_quotes: If view returns a string then surround it with extra
            quotes.

    Returns:
        flask.Response: JSONP response with javascript function call.

    Raises:
        ValueError: if return value is not supported.
        BadRequest: if callback is missing in URL query
            (if ``optional=False``).

    See Also:
        :func:`.json_response`,
        :func:`@as_json <flask_json.as_json>`.

        :ref:`JSON_JSONP_STRING_QUOTES <opt_jsonp_quotes>`,
        :ref:`JSON_JSONP_OPTIONAL <opt_jsonp_optional>`,
        :ref:`JSON_JSONP_QUERY_CALLBACKS <opt_jsonp_callbacks>`.
    """
    if f is None:
        def deco(func):
            @wraps(func)
            def wrapper(*args, **kw):
                rv = func(*args, **kw)
                return _json_p_handler(rv, callbacks, optional, add_quotes)
            return wrapper
        return deco

    else:
        @wraps(f)
        def wrapper2(*args, **kw):
            rv = f(*args, **kw)
            return _json_p_handler(rv, callbacks, optional, add_quotes)
        return wrapper2


# TODO: maybe subclass from HTTPException?
class JsonError(Exception):
    """Exception which will be converted to JSON response.

    Usage::

        raise JsonError(description='text')
        raise JsonError(status_=401, one='text', two=12)
    """
    def __init__(self, status_=400, headers_=None, **kwargs):
        """Construct error object.

        Parameters are the same as for :func:`.json_response`.

        Args:
            `status_`: HTTP response status code.
            `headers_`: iterable or dictionary with header values.
            kwargs: keyword arguments to put in result JSON.

        See Also:
            :func:`.json_response`,
            :meth:`@error_handler <.FlaskJSON.error_handler>`.
        """
        super(JsonError, self).__init__()
        assert status_ != 200
        self.status = status_
        self.headers = headers_
        self.data = kwargs


class JsonRequest(Request):
    """This class changes :class:`flask.Request` behaviour on JSON parse
    errors.

    :meth:`flask.Request.get_json` will raise :class:`.JsonError`
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
            raise JsonError(description=desc)
        else:
            raise JsonError()


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
        elif isinstance(o, collections_abc.Iterable):
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


class JsonTestResponse(Response):
    """JSON Response class for testing.

    It provides convenient access to JSON content without explicit response
    data decoding.

    Flask-JSON replaces Flask's response class with this one
    on initialization if testing mode enabled.

    Usage:

    .. code-block:: py

        app = Flask()
        app.config['TESTING'] = True
        FlaskJSON(app)
        ...
        client = app.test_client()
        r = client.get('/view')  # suppose it returns json_response(param='12)
        assert r.json['param'] == 12

    If you enable testing after Flask-JSON initialization the you have to
    set :class:`.JsonTestResponse` by yourself:

    .. code-block:: py

        app = Flask()
        FlaskJSON(app)
        app.config['TESTING'] = True
        app.response_class = JsonTestResponse

    """
    _json_cache = None

    @property
    def json(self):
        """Response JSON content."""
        if self._json_cache is None:
            assert self.mimetype == 'application/json'
            self._json_cache = json.loads(self.data)
        return self._json_cache


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
        return json_response(e.status, e.headers, **e.data)

    def init_app(self, app):
        """Initializes the application with the extension.

        Args:
            app: Flask application object.
        """
        app.config.setdefault('JSON_ADD_STATUS', True)
        app.config.setdefault('JSON_STATUS_FIELD_NAME', 'status')
        app.config.setdefault('JSON_DECODE_ERROR_MESSAGE', 'Not a JSON.')
        jsonify_errors = app.config.setdefault(
            'JSON_JSONIFY_HTTP_ERRORS', False)

        app.config.setdefault('JSON_JSONP_STRING_QUOTES', True)
        app.config.setdefault('JSON_JSONP_OPTIONAL', True)
        app.config.setdefault('JSON_JSONP_QUERY_CALLBACKS',
                              ['callback', 'jsonp'])

        if not hasattr(app, 'extensions'):
            app.extensions = dict()
        app.extensions['json'] = self

        self._app = app
        app.request_class = JsonRequest
        app.json_encoder = self._encoder_class
        app.errorhandler(JsonError)(self._error_handler)

        if jsonify_errors:
            self._jsonify_http_errors(app)

        if app.testing:
            app.response_class = JsonTestResponse

    def _jsonify_http_errors(self, app):
        """Force HTTP errors returned as JSON instead of default HTML."""
        status_field = app.config['JSON_STATUS_FIELD_NAME']

        def _handler(error, status_code, reason, default_description):
            response = {
                'reason': reason,
                'description': default_description,
            }
            if app.config['JSON_ADD_STATUS']:
                response[status_field] = status_code

            if isinstance(error, HTTPException) and error.description:
                response['description'] = error.description

            return json_response(status_code, data_=response)

        for code, exc in default_exceptions.items():
            if issubclass(exc, HTTPException):
                app.register_error_handler(code, partial(
                    _handler,
                    status_code=code,
                    reason=exc().name,
                    default_description=exc.description,
                ))

    def error_handler(self, func):
        """This decorator allows to set custom handler for the
        :class:`.JsonError` exceptions.

        In custom handler you may return :class:`flask.Response` or raise
        an exception. If user defined handler returns ``None`` then default
        action takes place (generate JSON response from the exception).

        Example:

            ::

                json = FlaskJson(app)
                ...

                @json.error_handler
                def custom_error_handler(e):
                    # e is JsonError.
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
        raises :class:`.JsonError`.

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
