Flask-JSON
==========

.. image:: https://github.com/skozlovf/flask-json/actions/workflows/test.yml/badge.svg?branch=master
   :target: https://github.com/skozlovf/flask-json/actions/workflows/test.yml

Flask-JSON is a simple extension that adds better JSON support to Flask
application.

Features:

* Works on python 3.3+ and Flask 2.2+.
* More ways to generate JSON responses (comparing to plain Flask).
* Extended JSON encoding support.

Usage
-----

Here is fast example:

.. code-block:: python

    from datetime import datetime
    from flask import Flask
    from flask_json import FlaskJSON, JsonError, json_response, as_json

    app = Flask(__name__)
    FlaskJSON(app)


    @app.route('/get_time')
    def get_time():
        return json_response(time=datetime.utcnow())


    @app.route('/get_time_and_value')
    @as_json
    def get_time_and_value():
        return dict(time=datetime.utcnow(), value=12)


    @app.route('/raise_error')
    def raise_error():
        raise JsonError(description='Example text.', code=123)


    if __name__ == '__main__':
        app.run()

Responses:

.. code-block:: json

    GET /get_time HTTP/1.1

    HTTP/1.0 200 OK
    Content-Type: application/json
    Content-Length: 60

    {
      "status": 200,
      "time": "2015-04-14T13:17:16.732000"
    }

.. code-block:: json

    GET /raise_error HTTP/1.1

    HTTP/1.0 400 BAD REQUEST
    Content-Type: application/json
    Content-Length: 70

    {
      "code": 123,
      "description": "Example text.",
      "status": 400
    }

Documentation
-------------

Documentation is available on
`Read the Docs <http://flask-json.readthedocs.io>`_.
