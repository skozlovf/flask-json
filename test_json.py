# -*- coding: utf-8 -*-
import unittest
from datetime import datetime, date, time, tzinfo, timedelta
from speaklater import make_lazy_string
from flask import Flask, request
from flask.json import loads, dumps
from flask_json import (
    json_response,
    FlaskJSON,
    JSONEncoderEx,
    JsonRequest,
    JsonErrorResponse
)


class InitTest(unittest.TestCase):
    """Initialization tests."""

    # Check initial state on create.
    def test_create(self):
        ext = FlaskJSON()
        self.assertIsNone(ext._app)
        self.assertIsNone(ext._error_handler_func)
        self.assertIsNone(ext._decoder_error_func)
        self.assertIs(ext._encoder_class, JSONEncoderEx)

    # Check initial config on init with constructor.
    def test_init_constructor(self):
        app = Flask(__name__)
        ext = FlaskJSON(app)

        self.assertEqual(app.config.get('JSON_ADD_STATUS'), True)
        self.assertIsNone(app.config.get('JSON_DATE_FORMAT'))
        self.assertIsNone(app.config.get('JSON_TIME_FORMAT'))
        self.assertIsNone(app.config.get('JSON_DATETIME_FORMAT'))
        self.assertEqual(app.config.get('JSON_DECODE_ERROR_MESSAGE'),
                         'Not a JSON.')
        self.assertIs(app.request_class, JsonRequest)
        self.assertIs(app.json_encoder, JSONEncoderEx)
        self.assertEqual(app.extensions['json'], ext)

    # Check initial config on deferred init.
    def test_init(self):
        app = Flask(__name__)
        ext = FlaskJSON()
        ext.init_app(app)

        self.assertEqual(app.config.get('JSON_ADD_STATUS'), True)
        self.assertIsNone(app.config.get('JSON_DATE_FORMAT'))
        self.assertIsNone(app.config.get('JSON_TIME_FORMAT'))
        self.assertIsNone(app.config.get('JSON_DATETIME_FORMAT'))
        self.assertEqual(app.config.get('JSON_DECODE_ERROR_MESSAGE'),
                         'Not a JSON.')
        self.assertIs(app.request_class, JsonRequest)
        self.assertIs(app.json_encoder, JSONEncoderEx)
        self.assertEqual(app.extensions['json'], ext)

    # Check decorators for uninitialized extension.
    def test_decorators(self):
        app = Flask(__name__)
        ext = FlaskJSON()

        @ext.error_handler
        def err_handler_func():
            pass

        @ext.decoder_error
        def decoder_func():
            pass

        @ext.encoder
        def encoder_func():
            pass

        self.assertEquals(ext._error_handler_func, err_handler_func)
        self.assertEquals(ext._decoder_error_func, decoder_func)

        # If FlaskJSON is not initialized with the app then only
        # '_encoder_class' will be set.
        self.assertIsNotNone(ext._encoder_class)
        self.assertIsNot(app.json_encoder, ext._encoder_class)

        # And after initialization we set our json encoder.
        ext.init_app(app)
        self.assertIs(app.json_encoder, ext._encoder_class)

    # Check decorators for initialized extension.
    def test_decorators_initialized(self):
        app = Flask(__name__)
        ext = FlaskJSON(app)

        @ext.decoder_error
        def decoder_func():
            pass

        # If we apply decorator on initialized extension then it sets
        # encoder class immediately.
        self.assertIs(app.json_encoder, ext._encoder_class)


class FlaskJsonTest(unittest.TestCase):
    """Logic tests."""
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.ext = FlaskJSON(self.app)
        self.client = self.ext._app.test_client()

    # Helper method to send JSON POST requests.
    def post_json(self, url, data, raw=False):
        content = data if raw else dumps(data)
        headers = [('Content-Type', 'application/json'),
                   ('Content-Length', len(content))]
        return self.client.post(url, headers=headers, data=content)

    # Check if JSON request is works.
    def test_json_request(self):
        @self.app.route('/test', methods=['POST'])
        def endpoint():
            data = request.get_json()
            return json_response(**data)

        r = self.post_json('/test', dict(some=42))
        self.assertEqual(r.status_code, 200)
        self.assertDictEqual(loads(r.data), dict(status=200, some=42))

    # Test json_response().
    def test_json_response(self):
        self.ctx = self.app.test_request_context()
        self.ctx.push()

        r = json_response()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, 'application/json')

        r = json_response(status=400)
        self.assertEqual(r.status_code, 400)

        # Response will contains status by default.
        r = json_response(some='val', data=42)
        self.assertEqual(r.status_code, 200)
        json = loads(r.data)
        self.assertDictEqual(json, {'status': 200, 'some': 'val', 'data': 42})

        # Disable status in response
        self.app.config['JSON_ADD_STATUS'] = False
        r = json_response(some='val', data=42)
        json = loads(r.data)
        self.assertDictEqual(json, {'some': 'val', 'data': 42})

        self.ctx.pop()

    # Test simple JsonErrorResponse.
    def test_json_error(self):
        @self.app.route('/test')
        def endpoint():
            raise JsonErrorResponse

        r = self.client.get('/test')
        self.assertEqual(r.status_code, 400)
        json = loads(r.data)
        self.assertDictEqual(json, {'status': 400})

        self.app.config['JSON_ADD_STATUS'] = False
        r = self.client.get('/test')
        self.assertEqual(r.status_code, 400)
        json = loads(r.data)
        self.assertDictEqual(json, {})

    # Test JsonErrorResponse with data.
    def test_json_error_with_data(self):
        @self.app.route('/test')
        def endpoint():
            raise JsonErrorResponse(info='Some info')

        r = self.client.get('/test')
        self.assertEqual(r.status_code, 400)
        json = loads(r.data)
        self.assertDictEqual(json, {'status': 400, 'info': 'Some info'})

        self.app.config['JSON_ADD_STATUS'] = False
        r = self.client.get('/test')
        self.assertEqual(r.status_code, 400)
        json = loads(r.data)
        self.assertDictEqual(json, {'info': 'Some info'})

    # Test JsonErrorResponse handler.
    def test_json_error_handler(self):
        @self.app.route('/test')
        def endpoint():
            raise JsonErrorResponse(info='Some info')

        # Just return error's info as HTTP 200.
        @self.ext.error_handler
        def handler(e):
            return e.data['info']

        r = self.client.get('/test')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, 'Some info')

    # Test response JSON encoder for datetime, date and time values.
    def test_encoder_datetime(self):
        class GMT1(tzinfo):
            def utcoffset(self, dt):
                return timedelta(hours=1)

            def dst(self, dt):
                return timedelta(0)

        @self.app.route('/test')
        def endpoint():
            dtm = datetime(2014, 05, 12, 17, 24, 10, tzinfo=GMT1())
            return json_response(tm1=time(12, 34, 56), tm2=time(1, 2, 3, 175),
                                 dt=date(2015, 12, 7),
                                 dtm=dtm)

        # By default ISO format is used.
        r = self.client.get('/test')
        self.assertEqual(r.status_code, 200)
        json = loads(r.data)
        self.assertEqual(json['tm1'], '12:34:56')
        self.assertEqual(json['tm2'], '01:02:03.000175')
        self.assertEqual(json['dt'], '2015-12-07')
        self.assertEqual(json['dtm'], '2014-05-12T17:24:10+01:00')

        # Custom formats.
        self.app.config['JSON_TIME_FORMAT'] = '%M:%S:%H'
        self.app.config['JSON_DATE_FORMAT'] = '%Y.%m.%d'
        self.app.config['JSON_DATETIME_FORMAT'] = '%Y/%m/%d %H-%M-%S'

        r = self.client.get('/test')
        self.assertEqual(r.status_code, 200)
        json = loads(r.data)
        self.assertEqual(json['tm1'], '34:56:12')
        self.assertEqual(json['tm2'], '02:03:01')
        self.assertEqual(json['dt'], '2015.12.07')
        self.assertEqual(json['dtm'], '2014/05/12 17-24-10')

    # Test encoding lazy string.
    def test_encoder_lazy(self):
        @self.app.route('/test')
        def endpoint():
            txt = u'Привет'
            return json_response(text=make_lazy_string(lambda: txt))

        r = self.client.get('/test')
        self.assertEqual(r.status_code, 200)
        json = loads(r.data)
        self.assertEqual(json['text'], u'Привет')

    # Test response JSON encoder with custom encoding.
    def test_encoder_hook(self):
        class Fake(object):
            data = 0

        @self.ext.encoder
        def my_encoder(o):
            if isinstance(o, Fake):
                return 'fake-%d' % o.data

        @self.app.route('/test')
        def endpoint():
            fake = Fake()
            fake.data = 42
            return json_response(fake=fake, tm=time(12, 34, 56), lst=[1, 2])

        r = self.client.get('/test')
        self.assertEqual(r.status_code, 200)
        json = loads(r.data)
        self.assertEqual(json['fake'], 'fake-42')
        self.assertEqual(json['tm'], '12:34:56')
        self.assertListEqual(json['lst'], [1, 2])

    # Test JsonRequest on invalid input JSON.
    def test_decoder_error(self):
        @self.app.route('/test', methods=['POST'])
        def endpoint():
            json = request.get_json()
            return json_response(**json)

        r = self.post_json('/test', data='bla', raw=True)
        self.assertEqual(r.status_code, 400)
        self.assertDictEqual(loads(r.data),
                             dict(status=400, description='Not a JSON.'))

        # Custom error message.
        self.app.config['JSON_DECODE_ERROR_MESSAGE'] = 'WTF?'
        r = self.post_json('/test', data='bla', raw=True)
        self.assertDictEqual(loads(r.data),
                             dict(status=400, description='WTF?'))

        # Custom decoder error handler - just return predefined dict instead of
        # raising an error.
        @self.ext.decoder_error
        def handler(e):
            return dict(text='hello')

        r = self.post_json('/test', data='bla', raw=True)
        self.assertDictEqual(loads(r.data), dict(status=200, text='hello'))


if __name__ == '__main__':
    unittest.main()
