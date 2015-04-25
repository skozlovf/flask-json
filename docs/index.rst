Flask-JSON
==========

Flask-JSON is a simple extension that adds better JSON support to Flask
application.

It helps to handle JSON-based requests and provides the following features:

* :func:`~flask_json.json_response` - function to generate JSON responses.
* :class:`~flask_json.JsonErrorResponse` - exception to generate JSON error
  responses.
* Extended JSON encoding support (see :ref:`encoding`).

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

Examples
--------

There are few examples are available on
`GitHub <https://github.com/skozlovf/flask-json/tree/master/examples>`_.

You also may take a look at
`tests <https://github.com/skozlovf/flask-json/tree/master/test_json.py>`_.

.. _encoding:

Encoding values
---------------

Flask-JSON supports encoding for several types out of the box and also provides
few ways to extend encoding.

iterables
^^^^^^^^^

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

time values
^^^^^^^^^^^

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

``JSON_*_FORMAT`` options allows to change result format.


translation strings
^^^^^^^^^^^^^^^^^^^

`speaklater's <https://pypi.python.org/pypi/speaklater>`_ ``_LazyString``
is used by `Flask-Babel <https://pythonhosted.org/Flask-Babel/>`_ and
`Flask-BabelEx <http://pythonhosted.org/Flask-BabelEx/>`_.

You can use it in JSON responses too, _LazyString will be converted to Unicode
string with translation::

    json_response(item=gettext('bla'))
    # {status=200, item='<translation>'}


custom objects
^^^^^^^^^^^^^^

To encode custom objects you can use
:meth:`@encoder <flask_json.FlaskJSON.encoder>` or implement special methods:
``__json__()`` or ``for_json()``::

    class MyJsonItem(object):
        def __json__(self):
            return '<__json__>'

    json_response(item=MyJsonItem())
    # {status=200, item='<__json__>'}

or::

    class MyJsonItem(object):
        def for_json(self):
            return '<for_json>'

    json_response(item=MyJsonItem())
    # {status=200, item='<for_json>'}

.. note:: To enable this approach you have to set
    :ref:`JSON_USE_ENCODE_METHODS <opt_use_enc_methods>` to ``True``.

Encoding order
^^^^^^^^^^^^^^

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

Configuration
-------------

You can configure Flask-JSON with the following options:

=============================   ================================================
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
