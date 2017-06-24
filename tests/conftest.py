import sys
import os.path
import pytest
from flask import Flask, json
from flask import __version__ as flask_ver
from flask.testing import FlaskClient as _FlaskClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import flask_json


class FlaskClient(_FlaskClient):
    """This class extends :class:`~flask.FlaskClient` with extra
    :meth:`post_json` to send JSON requests.
    """
    def post_json(self, url, data, raw=False):
        """Helper method to send JSON POST requests.

        Usage:

            client.post_json('/some/url', dict(param=value))
            client.post_json('/some/url', '{"param": "value"}', raw=True)

        Args:
            url: Target URL.
            data: Request payload. It maybe a dict or string with raw content.
            raw: If ``True`` then do not convert ``data`` to JSON string and use
                 it as is.

        Returns:
            flask_json.JsonTestResponse
        """
        content = data if raw else json.dumps(data)
        headers = [
            ('Content-Type', 'application/json'),
            ('Content-Length', len(content))
        ]
        return self.post(url, headers=headers, data=content)


@pytest.yield_fixture
def app():
    """This pytest fixture setups flask application
    and initializes Flask-JSON.
    """
    app = Flask(__name__)
    app.test_client_class = FlaskClient
    app.config['TESTING'] = True
    flask_json.FlaskJSON(app)
    yield app


@pytest.fixture
def client(app):
    """This pytest fixture creates Flask application test client.

    Note:
        Flask application and Flask-JSON will be setup too.

    See Also:
        :func:`app`
    """
    return app.test_client()


@pytest.yield_fixture
def app_request(app):
    """This pytest fixture setups Flask application test request context.

    Note:
        Flask application and Flask-JSON will be setup too.

    See Also:
        :func:`app`
    """
    ctx = app.test_request_context('/fake')
    ctx.push()
    yield ctx
    ctx.pop()


def pytest_namespace():
    return {
        'flask_ver': tuple(int(x) for x in flask_ver.split('.'))
    }
