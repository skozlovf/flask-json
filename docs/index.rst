==========
Flask-JSON
==========

Flask-JSON is a simple extension that adds better JSON support to Flask
application.

It helps to handle JSON-based requests and provides the following features:

* :func:`~flask_json.json_response` and :func:`@as_json <flask_json.as_json>`
  to generate JSON responses.
* :class:`~flask_json.JsonError` - exception to generate JSON error
  responses.
* Extended JSON encoding support (see :ref:`encoding`).
* :ref:`JSONP support <jsonp>` with :func:`@as_json_p <flask_json.as_json_p>`.

.. contents::
    :local:
    :backlinks: none

Installation
============

Install the extension with::

    $ easy_install Flask-JSON

or::

    $ pip install Flask-JSON


Initialization
==============

Before using Flask-JSON features you have to create
:class:`~flask_json.FlaskJSON` instance and initialize it with the Flask
application instance. As with common Flask extension there are two ways.

First way is to initialize the extension on construction::

    app = Flask(__name__)
    json = FlaskJSON(app)

Another way is to postpone initialization and pass Flask application to the
``init_app()`` method::

    app = Flask(__name__)
    json = FlaskJSON()
    ...
    json.init_app(app)

Flask-JSON provides few decorators and you can use them before and after
initialization::

    # Use decorator before initialization.
    json = FlaskJSON()

    @json.encoder
    def custom_encoder(o):
        pass

    json.init_app(app)

::

    # Use decorator after initialization.
    json = FlaskJSON(app)

    @json.encoder
    def custom_encoder(o):
        pass

Basic usage
===========

This section provides simple examples of usage with minimum comments just to
demonstrate basic features. Next sections describes features more detailed.

First example shows how to use :func:`~flask_json.json_response`,
:func:`@as_json <flask_json.as_json>` and :class:`~flask_json.JsonError` to
create JSON responses:

.. literalinclude:: ../examples/example2.py
   :language: python

Example responses::

    $ curl http://localhost:5000/get_time
    {"status": 200, "time": "2015-04-14T08:44:13.973000"}

    $ curl http://localhost:5000/get_value
    {"status": 200, "value": 12}

    $ curl -X POST --data 'bla' http://localhost:5000/increment_value
    {"status": 400, "description": "Not a JSON."}

    $ curl -X POST --data '{"value": "txt"}' http://localhost:5000/increment_value
    {"status": 400, "description": "Invalid value."}

    $ curl -X POST --data '{"value": 41}' http://localhost:5000/increment_value
    {"status": 200, "value": 42}

In more advanced example we change configuration and set custom error handler:

.. literalinclude:: ../examples/example3.py
   :language: python
   :lines: 1-15
   :append: # ... the rest is the same as before ...

Now responses looks like that::

    $ curl http://localhost:5000/get_time
    {"time": "14/04/2015 09:26:15"}

    $ curl -X POST --data 'bla' http://localhost:5000/increment_value
    {"hint": "RTFM"}

    $ curl -X POST --data '{"value": "txt"}' http://localhost:5000/increment_value
    {"description": "Invalid value."}

    $ curl -X POST --data '{"value": 41}' http://localhost:5000/increment_value
    {"value": 42}

Examples
========

There are few examples available on
`GitHub <https://github.com/skozlovf/flask-json/tree/master/examples>`_.

You also may take a look at
`tests <https://github.com/skozlovf/flask-json/tree/master/tests>`_.

.. _encoding:

Creating JSON responses
=======================

The main purpose of the Flask-JSON extension is to provide a convenient tool
for creating JSON responses. This section describes how you can do that.

Most important function to build JSON response is
:func:`~flask_json.json_response`. All other response related features uses it.

With :func:`~flask_json.json_response` you can:

* Create JSON response by passing keyword arguments::

    json_response(server_name='norris', available=True)

* Create JSON response with arrays or single values (*new in 0.3.2*)::

    json_response(data_=[1, 2, 3])
    json_response(data_=100500)

* Specify HTTP status code for response::

    json_response(status_=400, server_name='norris', available=True)

* Specify custom HTTP headers for response::

    json_response(server_name='norris', headers_={'X-STATUS': 'ok'})


By default :func:`~flask_json.json_response` adds HTTP status code to the
response JSON::

    {"status": 200, "server_name": "norris"}

but you can disable this or change status field name (see :ref:`config` for
more info).

Note what if you use ``data_`` then HTTP status is not added unless you pass
a dictionary.

Another way is to wrap a view with :func:`@as_json <flask_json.as_json>`
decorator and return json content::

    FlaskJSON(app)
    ...

    @as_json
    def my_view():
        return dict(server_name="norris")

    @as_json
    def my_view2():
        return [1, 2, 3]  # New in 0.3.2

The decorator calls :func:`~flask_json.json_response` internally and provides
the same features. You also can return HTTP status and headers::

    @as_json
    def my_view():
        return dict(server_name="norris"), 401, dict(MYHEADER=12)

:func:`@as_json <flask_json.as_json>` expects the following return values::

    @as_json
    def my_view():
        return json_content
        # or
        return json_content, http_status
        # or
        return json_content, custom_headers
        # or
        return json_content, http_status, custom_headers
        # or
        return json_content, custom_headers, http_status

``json_content`` may be ``None``, in such situation empty JSON response
will be generated::

    @as_json
    def my_view():
        do_some_stuff()

::

    @as_json
    def my_view():
        do_some_stuff()
        return None, 400  # same as {}, 400

If you return already created JSON response then it will be used as is::

    @as_json
    def my_view():
        do_some_stuff()
        return json_response(some=value)

    @as_json
    def my_view2():
        do_some_stuff()
        return json_response(_data=[1, 2, 3], headers_={'X-STATUS': 'ok'})

And one more way to create JSON response is to raise
:class:`~flask_json.JsonError`::

    def my_view():
        raise JsonError(error_description='Server is down')

It will generate HTTP 400 response with JSON payload.

:class:`~flask_json.JsonError`'s constructor has the same signature as
:func:`~flask_json.json_response` so you can force HTTP status and pass custom
headers::

    def my_view():
        raise JsonError(status_=401,
                        headers_=dict(MYHEADER=12, HEADER2='fail'),
                        error_description='Server is down')

Jsonify HTTP errors
-------------------

:ref:`JSON_JSONIFY_HTTP_ERRORS <opt_jsonify_http_errors>` option allows to
force returning all standard HTTP errors as JSON.

Now response looks this way::

    $ curl http://localhost:5000
    {"description":"The server encountered an internal error and was unable to complete your request.  Either the server is overloaded or there is an error in the application.", "reason":"Internal Server Error", "status":500}

Encoding values
===============

Flask-JSON supports encoding for several types out of the box and also provides
few ways to extend it.

Iterables
---------

Any iterable type will be converted to list value::

    # set object
    json_response(items=set([1, 2, 3]))
    # {status=200, items=[1, 2, 3]}

    # generator
    json_response(items=(x for x in [3, 2, 42]))
    # {status=200, items=[3, 2, 42]}

    # iterator
    json_response(lst=iter([1, 2, 3]))
    # {status=200, items=[1, 2, 3]}

Time values
-----------

:class:`~datetime.datetime`, :class:`~datetime.date` and :class:`~datetime.time`
will be converted to ISO 8601 or custom format depending on configuration::

    json_response(datetime=datetime(2014, 5, 12, 17, 24, 10),
                  date=date(2015, 12, 7),
                  time=time(12, 34, 56))
    # {
    #   "status": 200,
    #   "datetime": "2014-05-12T17:24:10",
    #   "date": "2015-12-07",
    #   "time": "12:34:56"
    # }

:ref:`JSON_*_FORMAT <opt_fmt_datetime>` options allows to change result format.

Translation strings
-------------------

`speaklater's <https://pypi.python.org/pypi/speaklater>`_ ``_LazyString``
is used by `Flask-Babel <https://pythonhosted.org/Flask-Babel/>`_ and
`Flask-BabelEx <http://pythonhosted.org/Flask-BabelEx/>`_.

You can use it in JSON responses too, _LazyString will be converted to Unicode
string with translation::

    json_response(item=gettext('bla'))
    # {status=200, item='<translation>'}


Custom types
------------

To encode custom types you can implement special methods
``__json__()`` or ``for_json()``::

    class MyJsonItem(object):
        def __json__(self):
            return '<__json__>'

    def view():
        return json_response(item=MyJsonItem())
        # {status=200, item='<__json__>'}

::

    class MyJsonItem(object):
        def for_json(self):
            return '<for_json>'

    def view():
        return json_response(item=MyJsonItem())
        # {status=200, item='<for_json>'}

.. note:: To enable this approach you have to set
    :ref:`JSON_USE_ENCODE_METHODS <opt_use_enc_methods>` to ``True``.

Another way is to use :meth:`@encoder <flask_json.FlaskJSON.encoder>`
decorator::

    @json.encoder
    def encoder(o):
        if isinstance(o, MyClass):
            return o.to_string()

    def view():
        return json_response(value=MyClass())


Encoding order
--------------

Flask-JSON calls encoders in the following order:


* User defined :meth:`@encoder <flask_json.FlaskJSON.encoder>`.
* Flask-JSON encoders:
    * ``_LazyString``
    * iterables
    * :class:`~datetime.datetime`
    * :class:`~datetime.date`
    * :class:`~datetime.time`
    * ``__json__()`` method
    * ``for_json()`` method
* Flask encoders.

Errors handing
==============

Flask-JSON allows you to change default behaviour related to errors handing
by using the following decorators:

:meth:`@invalid_json_error <flask_json.FlaskJSON.invalid_json_error>` - allows
to handle invalid JSON requests::

    json = FlaskJSON(app)
    ...

    @json.invalid_json_error
    def handler(e):
        # e - original exception.
        raise SomeThing
    ...

    def view():
        # This call runs handler() on invalid JSON.
        data = request.get_json()
        ...

:meth:`@error_handler <flask_json.FlaskJSON.error_handler>` -
allows to handle :class:`.JsonError` exceptions::

    json = FlaskJSON(app)
    ...

    @json.error_handler
    def error_handler(e):
        # e - JsonError.
        return json_response(401, text='Something wrong.')

.. _jsonp:

JSONP support
=============

If you want to generate JSONP responses then you can use
:func:`@as_json_p <flask_json.as_json_p>` decorator.

It expects callback name in the URL query and returns response with
javascript function call.

Wrapped view must follow the same requirements as for
:func:`@as_json <flask_json.as_json>`, additionally string value is supported.

Example:

.. literalinclude:: ../examples/example4.py
   :language: python

Example responses::

    $ curl http://localhost:5000/message/hello?callback=alert
    alert("hello");

    $ curl http://localhost:5000/quote_message?callback=alert
    alert("Hello, \"Sam\".");

    $ curl http://localhost:5000/dict?callback=alert
    alert({
      "param": 42
    });

You may change default :func:`@as_json_p <flask_json.as_json_p>` behaviour with
configurations :ref:`JSON_JSONP_STRING_QUOTES <opt_jsonp_quotes>`,
:ref:`JSON_JSONP_OPTIONAL <opt_jsonp_optional>` and
:ref:`JSON_JSONP_QUERY_CALLBACKS <opt_jsonp_callbacks>`.

Also there is a possibility to set configuration for the specific view via
decorator parameters.

Testing
=======

Flask-JSON also may help in testing of your JSON API calls. It replaces
Flask's :class:`~flask.Response` class with custom one if ``TESTING`` config
flag is enabled.

With Flask-JSON response class :class:`~flask_json.JsonTestResponse` you can
use :attr:`~flask_json.JsonTestResponse.json` attribute.
Here is example test project:

.. literalinclude:: ../examples/example_test.py
   :language: python

.. _config:

Configuration
=============

You can configure Flask-JSON with the following options:

==============================  ================================================
``JSON_ADD_STATUS``             .. _opt_add_status:

                                Put HTTP status field in all JSON responses.

                                Name of the field depends on
                                :ref:`JSON_STATUS_FIELD_NAME <opt_status_name>`.

                                See :func:`~flask_json.json_response` for more
                                info.

                                Default: ``True``.

``JSON_STATUS_FIELD_NAME``      .. _opt_status_name:

                                Name of the field with HTTP status in
                                JSON response.

                                This field is present only if
                                :ref:`JSON_ADD_STATUS <opt_add_status>` is
                                enabled.

                                See :func:`~flask_json.json_response` for more
                                info.

                                Default: ``status``.

``JSON_DECODE_ERROR_MESSAGE``   .. _opt_decode_error_msg:

                                Default error response message for the invalid
                                JSON request.

                                If the message is not ``None`` and not empty
                                then ``description`` field will be added to
                                JSON response.

                                Default: ``Not a JSON``.

``JSON_DATETIME_FORMAT``        .. _opt_fmt_datetime:

                                Format for the :class:`datetime` values in JSON
                                response.

                                Default is ISO 8601:

                                | ``YYYY-MM-DDTHH:MM:SS``
                                | or
                                | ``YYYY-MM-DDTHH:MM:SS.mmmmmm``.

                                Note what it differs from the default Flask
                                behaviour where :class:`~datetime.datetime`
                                is represented in RFC1123 format:

                                | ``Wdy, DD Mon YYYY HH:MM:SS GMT``.

``JSON_DATE_FORMAT``            .. _opt_fmt_date:

                                Format for the :class:`~datetime.date` values
                                in JSON response.

                                Default is ISO 8601: ``YYYY-MM-DD``.

``JSON_TIME_FORMAT``            .. _opt_fmt_time:

                                Format for the :class:`~datetime.time` values
                                in JSON response.

                                Default is ISO 8601: ``HH-MM-SS``.

``JSON_USE_ENCODE_METHODS``     .. _opt_use_enc_methods:

                                Check for ``__json__()`` and ``for_json()``
                                object methods while JSON encoding.

                                This allows to support custom objects in JSON
                                response.

                                Default: ``False``.

``JSON_JSONP_STRING_QUOTES``    .. _opt_jsonp_quotes:

                                If a view returns a string then surround it
                                with extra quotes.

                                Default: ``True``.

``JSON_JSONP_OPTIONAL``         .. _opt_jsonp_optional:

                                Make JSONP optional. If no callback is passed
                                then fallback to JSON response as with
                                :func:`@as_json <flask_json.as_json>`.

                                Default: ``True``.

``JSON_JSONP_QUERY_CALLBACKS``  .. _opt_jsonp_callbacks:

                                List of allowed JSONP callback query parameters.

                                Default: ``['callback', 'jsonp']``.

``JSON_JSONIFY_HTTP_ERRORS``    .. _opt_jsonify_http_errors:

                                Return standard HTTP Errors as JSON instead of
                                HTML by default.

                                Note: this will register custom error handler
                                in Flask. So, this option should be set before
                                the init of FlaskJSON.

                                Default: ``False``.
==============================  ================================================

See :ref:`python:strftime-strptime-behavior` for more info about time related
formats.


API
===

This section describes Flask-JSON functions and classes.

.. autoclass:: flask_json.FlaskJSON
    :members:

.. autofunction:: flask_json.json_response

.. autofunction:: flask_json.as_json

.. autofunction:: flask_json.as_json_p

.. autoclass:: flask_json.JsonError
    :members:
    :special-members: __init__

.. autoclass:: flask_json.JsonTestResponse
    :members:
    :special-members: __init__

Low-Level API
-------------

.. autoclass:: flask_json.JsonRequest
    :members:

.. autoclass:: flask_json.JSONEncoderEx
    :members:

.. include:: ../CHANGES
