Flask-JSON
==========

Flask-JSON is a simple extension that adds better JSON support to Flask
application.

It helps to handle JSON-based requests and provides the following features:

* :func:`~flask_json.json_response` - function to generate JSON responses.
* :class:`~flask_json.JsonErrorResponse` - exception to generate JSON error
  responses.
* Support of the python's :class:`~datetime.datetime`, :class:`~datetime.date`,
  :class:`~datetime.time` and
  `speaklater's <https://pypi.python.org/pypi/speaklater>`_ lazy strings
  in JSON responses.

Installation
------------

Install the extension with::

    $ easy_install Flask-JSON

or::

    $ pip install Flask-JSON


Usage
-----

Next example illustrates basic features:

.. literalinclude:: ../examples/example2.py
   :language: python

Example requests::

    $ curl http://localhost:5000/get_time
    {"status": 200, "time": "2015-04-14T08:44:13.973000"}

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

Examples are available on
`GitHub <https://github.com/skozlovf/flask-json/tree/master/examples>`_.


Configuration
-------------

You can configure Flask-JSON with the following options:

=============================   ================================================
``JSON_ADD_STATUS``             .. _opt_add_status:

                                Put ``status`` field in all JSON
                                responses.

                                Default: ``True``.

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
=============================   ================================================

See :ref:`python:strftime-strptime-behavior` for more info about time related
formats.

Decorators
----------

In addition to configuration options Flask-JSON allows you to change default
behaviour with decorators:

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
allows to handle :class:`.JsonErrorResponse` exceptions::

    json = FlaskJSON(app)
    ...

    @json.error_handler
    def error_handler(e):
        # e - JsonErrorResponse.
        return json_response(401, text='Something wrong.')

:meth:`@encoder <flask_json.FlaskJSON.encoder>` -  allows to extend JSON
encoder with custom types::

    json = FlaskJSON(app)
    ...

    @json.encoder
    def encoder(o):
        if isinstance(o, MyClass):
            return o.to_string()
    ...

    def view():
        return json_response(value=MyClass())

API
---

This section describes Flask-JSON functions and classes.

.. autoclass:: flask_json.FlaskJSON
    :members:

.. autofunction:: flask_json.json_response

.. autoclass:: flask_json.JsonErrorResponse
    :members:

Low-Level API
^^^^^^^^^^^^^

.. autoclass:: flask_json.JsonRequest
    :members:

.. autoclass:: flask_json.JSONEncoderEx
    :members:
