import unittest
from flask import Flask
from flask_json import json_response, FlaskJSON, JsonTestResponse


def our_app():
    app = Flask(__name__)
    app.test_value = 0
    FlaskJSON(app)

    @app.route('/increment')
    def increment():
        app.test_value += 1
        return json_response(value=app.test_value)

    return app


class OurAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = our_app()
        self.app.config['TESTING'] = True

        # We have to change response class manually since TESTING flag is
        # set after Flask-JSON initialization.
        self.app.response_class = JsonTestResponse
        self.client = self.app.test_client()

    def test_app(self):
        r = self.client.get('/increment')

        # Here is how we can access to JSON.
        assert 'value' in r.json
        assert r.json['value'] == 1


if __name__ == '__main__':
    unittest.main()
