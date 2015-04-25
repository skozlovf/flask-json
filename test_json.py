# -*- coding: utf-8 -*-
from datetime import datetime, date, time, tzinfo, timedelta
try:
    from speaklater import make_lazy_string
except ImportError:
    make_lazy_string = None
from flask import Flask, request, json
import flask_json
from flask_json import (
    json_response,
    FlaskJSON,
    JSONEncoderEx,
    JsonRequest,
    JsonErrorResponse
)
from nose.tools import assert_equals, assert_true

# To support python 2.6 tests we have to add few missing functions.
import sys
if sys.version_info < (2, 7):
    def assert_is(a, b):
        assert a is b

    def assert_is_not(a, b):
        assert a is not b

    def assert_is_none(a):
        assert a is None

    def assert_is_not_none(a):
        assert a is not None

    def assert_dict_equal(a, b):
        diff = set(a.iteritems()) - set(b.iteritems())
        assert not diff, 'dicts are different'
else:
    from nose.tools import (
        assert_is,
        assert_is_not,
        assert_is_none,
        assert_is_not_none,
        assert_dict_equal
    )


# -- Initialization tests ------------------------------------------------------

# Check initial state on create.
def test_create():
    ext = FlaskJSON()
    assert_is_none(ext._app)
    assert_is_none(ext._error_handler_func)
    assert_is_none(ext._decoder_error_func)
    assert_is(ext._encoder_class, JSONEncoderEx)


# Check initial config on init with constructor.
def test_init_constructor():
    app = Flask(__name__)
    ext = FlaskJSON(app)

    assert_equals(app.config.get('JSON_ADD_STATUS'), True)
    assert_is_none(app.config.get('JSON_DATE_FORMAT'))
    assert_is_none(app.config.get('JSON_TIME_FORMAT'))
    assert_is_none(app.config.get('JSON_DATETIME_FORMAT'))
    assert_equals(app.config.get('JSON_DECODE_ERROR_MESSAGE'), 'Not a JSON.')
    assert_is(app.request_class, JsonRequest)
    assert_is(app.json_encoder, JSONEncoderEx)
    assert_equals(app.extensions['json'], ext)


# Check initial config on deferred init.
def test_init():
    app = Flask(__name__)
    ext = FlaskJSON()
    ext.init_app(app)

    assert_equals(app.config.get('JSON_ADD_STATUS'), True)
    assert_is_none(app.config.get('JSON_DATE_FORMAT'))
    assert_is_none(app.config.get('JSON_TIME_FORMAT'))
    assert_is_none(app.config.get('JSON_DATETIME_FORMAT'))
    assert_equals(app.config.get('JSON_DECODE_ERROR_MESSAGE'), 'Not a JSON.')
    assert_is(app.request_class, JsonRequest)
    assert_is(app.json_encoder, JSONEncoderEx)
    assert_equals(app.extensions['json'], ext)


# Check decorators for uninitialized extension.
def test_decorators():
    app = Flask(__name__)
    ext = FlaskJSON()

    @ext.error_handler
    def err_handler_func():
        pass

    @ext.invalid_json_error
    def decoder_func():
        pass

    @ext.encoder
    def encoder_func():
        pass

    assert_equals(ext._error_handler_func, err_handler_func)
    assert_equals(ext._decoder_error_func, decoder_func)

    # If FlaskJSON is not initialized with the app then only
    # '_encoder_class' will be set.
    assert_is_not_none(ext._encoder_class)
    assert_is_not(app.json_encoder, ext._encoder_class)

    # And after initialization we set our json encoder.
    ext.init_app(app)
    assert_is(app.json_encoder, ext._encoder_class)


# Check decorators for initialized extension.
def test_decorators_initialized():
    app = Flask(__name__)
    ext = FlaskJSON(app)

    @ext.invalid_json_error
    def decoder_func():
        pass

    # If we apply decorator on initialized extension then it sets
    # encoder class immediately.
    assert_is(app.json_encoder, ext._encoder_class)


# -- Logic tests ---------------------------------------------------------------

class TestLogic(object):
    def setup(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.ext = FlaskJSON(self.app)
        self.client = self.ext._app.test_client()

    # Helper method to send JSON POST requests.
    def post_json(self, url, data, raw=False):
        content = data if raw else json.dumps(data)
        headers = [
            ('Content-Type', 'application/json'),
            ('Content-Length', len(content))
        ]
        return self.client.post(url, headers=headers, data=content)

    # Check if JSON request is works.
    def test_json_request(self):
        @self.app.route('/test', methods=['POST'])
        def endpoint():
            data = request.get_json()
            return json_response(**data)

        r = self.post_json('/test', dict(some=42))
        assert_equals(r.status_code, 200)
        assert_dict_equal(json.loads(r.data), dict(status=200, some=42))

    # Test json_response().
    def test_json_response(self):
        with self.app.test_request_context():
            r = json_response()
            assert_equals(r.status_code, 200)
            assert_equals(r.mimetype, 'application/json')

            r = json_response(status=400)
            assert_equals(r.status_code, 400)

            # Response will contains status by default.
            r = json_response(some='val', data=42)
            assert_equals(r.status_code, 200)
            data = json.loads(r.data)
            assert_dict_equal(data, {'status': 200, 'some': 'val', 'data': 42})

            # Disable status in response.
            self.app.config['JSON_ADD_STATUS'] = False
            r = json_response(some='val', data=42)
            data = json.loads(r.data)
            assert_dict_equal(data, {'some': 'val', 'data': 42})

    # Test simple JsonErrorResponse.
    def test_json_error(self):
        @self.app.route('/test')
        def endpoint():
            raise JsonErrorResponse

        r = self.client.get('/test')
        assert_equals(r.status_code, 400)
        data = json.loads(r.data)
        assert_dict_equal(data, {'status': 400})

        self.app.config['JSON_ADD_STATUS'] = False
        r = self.client.get('/test')
        assert_equals(r.status_code, 400)
        data = json.loads(r.data)
        assert_dict_equal(data, {})

    # Test JsonErrorResponse with data.
    def test_json_error_with_data(self):
        @self.app.route('/test')
        def endpoint():
            raise JsonErrorResponse(info='Some info')

        r = self.client.get('/test')
        assert_equals(r.status_code, 400)
        data = json.loads(r.data)
        assert_dict_equal(data, {'status': 400, 'info': 'Some info'})

        self.app.config['JSON_ADD_STATUS'] = False
        r = self.client.get('/test')
        assert_equals(r.status_code, 400)
        data = json.loads(r.data)
        assert_dict_equal(data, {'info': 'Some info'})

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
        assert_equals(r.status_code, 200)
        # On python 3 Response.data is a byte object, so to compare we have to
        # convert it to unicode.
        if sys.version_info > (2, 7):
            assert_equals(r.data.decode('utf-8'), 'Some info')
        else:
            assert_equals(r.data, 'Some info')

    # Test encoding lazy string.
    def test_encoder_lazy(self):
        # Do nothing if speaklater is not installed.
        if make_lazy_string is None:
            return

        @self.app.route('/test')
        def endpoint():
            txt = u'Привет'
            return json_response(text=make_lazy_string(lambda: txt))

        r = self.client.get('/test')
        assert_equals(r.status_code, 200)
        data = json.loads(r.data)
        assert_equals(data['text'], u'Привет')

    # Test encoding iterable types: set, generators, iterators.
    def test_encoder_iterable(self):
        with self.app.test_request_context():
            # set
            r = json_response(lst=set([1, 2, 3]))
            data = json.loads(r.data)
            assert_equals(data['lst'], [1, 2, 3])

            # generator
            r = json_response(lst=(x for x in [3, 2, 42]))
            data = json.loads(r.data)
            assert_equals(data['lst'], [3, 2, 42])

            # iterator
            r = json_response(lst=iter([1, 2, 3]))
            data = json.loads(r.data)
            assert_equals(data['lst'], [1, 2, 3])

    # Test encoding if speaklater is not installed.
    # Here we just check if JSONEncoderEx.default() runs without errors.
    def test_encoder_nospeaklater(self):
        @self.app.route('/test')
        def endpoint():
            return json_response(text=time())  # this calls our encoder.

        # Let's pretend we have no speaklater imported
        # to test behaviour without speaklater even if it installed.
        flask_json._LazyString = None

        r = self.client.get('/test')
        assert_equals(r.status_code, 200)
        data = json.loads(r.data)
        assert_equals(data['text'], '00:00:00')

    # Test response JSON encoder for datetime, date and time values.
    def test_encoder_datetime(self):
        class GMT1(tzinfo):
            def utcoffset(self, dt):
                return timedelta(hours=1)

            def dst(self, dt):
                return timedelta(0)

        @self.app.route('/test')
        def endpoint():
            dtm = datetime(2014, 5, 12, 17, 24, 10, tzinfo=GMT1())
            return json_response(tm1=time(12, 34, 56), tm2=time(1, 2, 3, 175),
                                 dt=date(2015, 12, 7), dtm=dtm)

        # By default ISO format is used.
        r = self.client.get('/test')
        assert_equals(r.status_code, 200)
        data = json.loads(r.data)
        assert_equals(data['tm1'], '12:34:56')
        assert_equals(data['tm2'], '01:02:03.000175')
        assert_equals(data['dt'], '2015-12-07')
        assert_equals(data['dtm'], '2014-05-12T17:24:10+01:00')

        # Custom formats.
        self.app.config['JSON_TIME_FORMAT'] = '%M:%S:%H'
        self.app.config['JSON_DATE_FORMAT'] = '%Y.%m.%d'
        self.app.config['JSON_DATETIME_FORMAT'] = '%Y/%m/%d %H-%M-%S'

        r = self.client.get('/test')
        assert_equals(r.status_code, 200)
        data = json.loads(r.data)
        assert_equals(data['tm1'], '34:56:12')
        assert_equals(data['tm2'], '02:03:01')
        assert_equals(data['dt'], '2015.12.07')
        assert_equals(data['dtm'], '2014/05/12 17-24-10')

    # Test if __json__() and for_json() is disabled by default.
    def test_encoder_obj(self):
        class MyJsonItem(object):
            val = None

            def __init__(self, val=None):
                self.val = val

            def __json__(self):
                return '<empty>' if self.val is None else str(self.val)

        with self.app.test_request_context():
            try:
                json_response(item=MyJsonItem())
                has_exception = False
            except TypeError:
                has_exception = True
            assert_true(has_exception)

    # Test __json__().
    def test_encoder_obj_json(self):
        # To use __json__() and for_json() we have to set this config.
        self.app.config['JSON_USE_ENCODE_METHODS'] = True

        class MyJsonItem(object):
            def __json__(self):
                return '<__json__>'

        with self.app.test_request_context():
            r = json_response(item=MyJsonItem())
            data = json.loads(r.data)
            assert_equals(data['item'], '<__json__>')

    # Test for_json().
    def test_encoder_obj_for_json(self):
        self.app.config['JSON_USE_ENCODE_METHODS'] = True

        class MyJsonItem(object):
            def for_json(self):
                return '<for_json>'

        with self.app.test_request_context():
            r = json_response(item=MyJsonItem())
            data = json.loads(r.data)
            assert_equals(data['item'], '<for_json>')

    # Test if __json__() calles before for_json().
    def test_encoder_obj_priority(self):
        self.app.config['JSON_USE_ENCODE_METHODS'] = True

        class MyJsonItem(object):
            def __json__(self):
                return '<__json__>'

            def for_json(self):
                return '<for_json>'

        with self.app.test_request_context():
            r = json_response(item=MyJsonItem())
            data = json.loads(r.data)
            assert_equals(data['item'], '<__json__>')

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
            return json_response(fake=fake, tm=time(12, 34, 56), txt='txt')

        r = self.client.get('/test')
        assert_equals(r.status_code, 200)
        data = json.loads(r.data)
        assert_equals(data['fake'], 'fake-42')
        assert_equals(data['tm'], '12:34:56')
        assert_equals(data['txt'], 'txt')

    # Check if JSONEncoderEx calls original default() method.
    # In such situation exception will be raised (not serializable).
    def test_encoder_invalid(self):
        @self.app.route('/test')
        def endpoint():
            try:
                json_response(fake=object())
            except TypeError:
                return json_response(fake=42)
            return json_response(fake=1)

        r = self.client.get('/test')
        assert_equals(r.status_code, 200)
        data = json.loads(r.data)
        assert_equals(data['fake'], 42)

    # Test JsonRequest on invalid input JSON.
    def test_decoder_error(self):
        @self.app.route('/test', methods=['POST'])
        def endpoint():
            data = request.get_json()
            return json_response(**data)

        r = self.post_json('/test', data='bla', raw=True)
        assert_equals(r.status_code, 400)
        assert_dict_equal(json.loads(r.data),
                          dict(status=400, description='Not a JSON.'))

        # Custom error message.
        self.app.config['JSON_DECODE_ERROR_MESSAGE'] = 'WTF?'
        r = self.post_json('/test', data='bla', raw=True)
        assert_dict_equal(json.loads(r.data),
                          dict(status=400, description='WTF?'))

        # Empty error message.
        self.app.config['JSON_DECODE_ERROR_MESSAGE'] = None
        r = self.post_json('/test', data='bla', raw=True)
        assert_dict_equal(json.loads(r.data), dict(status=400))

        # Custom decoder error handler - just return predefined dict instead of
        # raising an error.
        @self.ext.invalid_json_error
        def handler(e):
            return dict(text='hello')

        r = self.post_json('/test', data='bla', raw=True)
        assert_dict_equal(json.loads(r.data), dict(status=200, text='hello'))

        # Decoder with no action (nothing is raised or returned) - go back to
        # default behaviour.
        @self.ext.invalid_json_error
        def handler2(e):
            pass

        r = self.post_json('/test', data='bla', raw=True)
        assert_dict_equal(json.loads(r.data), dict(status=400))
