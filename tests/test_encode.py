# -*- coding: utf-8 -*-
"""
This module provides tests for Flask-JSON encoding feature.
"""
import pytest
from datetime import datetime, date, time, tzinfo, timedelta
import flask_json
from flask_json import json_response


@pytest.mark.usefixtures('app_request')
class TestEncode(object):
    # Test: encode dict.
    def test_dict(self):
        r = json_response(data_={'one': 'two', 'three': 'four'})
        assert r.status_code, 200
        assert r.json == {'status': 200, 'one': 'two', 'three': 'four'}

    # Test: encode dict with numeric keys.
    def test_dict_num_keys(self):
        r = json_response(data_={1: 2, 3: 4}, add_status_=False)
        assert r.status_code, 200
        assert r.json == {'1': 2, '3': 4}

    # Test: encode lazy string.
    def test_lazystring(self):
        speaklater = pytest.importorskip("speaklater")
        # test_nospeaklater() overrides this import so we have to revert it
        # otherwise the test may fail because flask_json._LazyString
        # will be None
        flask_json._LazyString = speaklater._LazyString

        r = json_response(text=speaklater.make_lazy_string(lambda: u'Привет'))
        assert r.status_code, 200
        assert r.json['text'] == u'Привет'

    # Test: encode iterable types: set, generators, iterators.
    # All of the must be converted to array of values.
    def test_iterable(self):
        # set
        r = json_response(lst=set([1, 2, 3]))
        assert r.json['lst'] == [1, 2, 3]

        # generator
        r = json_response(lst=(x for x in [3, 2, 42]))
        assert r.json['lst'] == [3, 2, 42]

        # iterator
        r = json_response(lst=iter([1, 2, 3]))
        assert r.json['lst'] == [1, 2, 3]

    # Test: encode stuff if speaklater is not installed.
    # Here we just check if JSONEncoderEx.default() runs without errors.
    def test_nospeaklater(self):
        # Let's pretend we have no speaklater imported to test behaviour
        # without speaklater even if it installed.
        flask_json._LazyString = None

        r = json_response(text=time())
        assert r.status_code == 200
        assert r.json['text'] == '00:00:00'

    # Helper function to build response with time values.
    # Used by test_datetime_*().
    @staticmethod
    def get_time_values():
        class GMT1(tzinfo):
            def utcoffset(self, dt):
                return timedelta(hours=1)

            def dst(self, dt):
                return timedelta(0)

        dtm = datetime(2014, 5, 12, 17, 24, 10, tzinfo=GMT1())
        return json_response(tm1=time(12, 34, 56), tm2=time(1, 2, 3, 175),
                             dt=date(2015, 12, 7), dtm=dtm)

    # Test: encode datetime, date and time values with default format.
    # By default, flask converts to RFC 2822.
    def test_datetime_default_format(self):
        r = TestEncode.get_time_values()
        assert r.status_code == 200
        assert r.json['tm1'] == '12:34:56'
        assert r.json['tm2'] == '01:02:03.000175'
        assert r.json['dt'] == 'Mon, 07 Dec 2015 00:00:00 GMT'
        assert r.json['dtm'] == 'Mon, 12 May 2014 16:24:10 GMT'

    # Test: encode datetime, date and time values with default format.
    # Use ISO format.
    def test_datetime_iso_format(self, app):
        app.config['JSON_DATE_FORMAT'] = 'iso'
        app.config['JSON_DATETIME_FORMAT'] = 'iso'
        r = TestEncode.get_time_values()
        assert r.status_code == 200
        assert r.json['tm1'] == '12:34:56'
        assert r.json['tm2'] == '01:02:03.000175'
        assert r.json['dt'] == '2015-12-07'
        assert r.json['dtm'] == '2014-05-12T17:24:10+01:00'

    # Test: encode datetime, date and time values with custom format.
    def test_datetime_custom_format(self, app):
        app.config['JSON_TIME_FORMAT'] = '%M:%S:%H'
        app.config['JSON_DATE_FORMAT'] = '%Y.%m.%d'
        app.config['JSON_DATETIME_FORMAT'] = '%Y/%m/%d %H-%M-%S'

        r = TestEncode.get_time_values()
        assert r.status_code == 200
        assert r.json['tm1'] == '34:56:12'
        assert r.json['tm2'] == '02:03:01'
        assert r.json['dt'] == '2015.12.07'
        assert r.json['dtm'] == '2014/05/12 17-24-10'

    # Test: encode custom type, check if __json__() is not used by default.
    def test_custom_obj_default_json(self):
        class MyJsonItem(object):
            def __json__(self):
                return '<__json__>'

        with pytest.raises(TypeError) as e:
            json_response(item=MyJsonItem())
        assert str(e.value).endswith(' is not JSON serializable')

    # Test: encode custom type, check if for_json() is not used by default.
    def test_custom_obj_default_for_json(self):
        class MyJsonItem(object):
            def for_json(self):
                return '<for_json>'

        with pytest.raises(TypeError) as e:
            json_response(item=MyJsonItem())
        assert str(e.value).endswith(' is not JSON serializable')

    # Test: encode custom type with __json__().
    def test_custom_obj_json(self, app):
        class MyJsonItem(object):
            def __json__(self):
                return '<__json__>'

        # To use __json__() and for_json() we have to set this config.
        app.config['JSON_USE_ENCODE_METHODS'] = True
        r = json_response(item=MyJsonItem())
        assert r.json['item'] == '<__json__>'

    # Test: encode custom type with for_json().
    def test_custom_obj_for_json(self, app):
        class MyJsonItem(object):
            def for_json(self):
                return '<for_json>'

        app.config['JSON_USE_ENCODE_METHODS'] = True
        r = json_response(item=MyJsonItem())
        assert r.json['item'] == '<for_json>'

    # Test: if __json__() gets called before for_json().
    def test_custom_obj_priority(self, app):
        class MyJsonItem(object):
            def __json__(self):
                return '<__json__>'
            def for_json(self):
                return '<for_json>'

        app.config['JSON_USE_ENCODE_METHODS'] = True
        r = json_response(item=MyJsonItem())
        assert r.json['item'] == '<__json__>'

    # Test: non-serializable object if JSON_USE_ENCODE_METHODS is set.
    def test_custom_obj_err(self, app):
        class MyItem(object):
            pass

        app.config['JSON_USE_ENCODE_METHODS'] = True
        with pytest.raises(TypeError) as e:
            json_response(item=MyItem())
        assert str(e.value).endswith(' is not JSON serializable')

    # Test: encoder with custom encoding function.
    def test_hook(self, app):
        class Fake(object):
            data = 0

        # Encode custom type with encoding hook.
        # This way is additional to __json__() and for_json().

        encoder = app.extensions['json'].encoder

        @encoder
        def my_encoder(o):
            if isinstance(o, Fake):
                return 'fake-%d' % o.data

        fake = Fake()
        fake.data = 42
        r = json_response(fake=fake, tm=time(12, 34, 56), txt='txt')
        assert r.status_code == 200
        assert r.json['fake'] == 'fake-42'
        assert r.json['tm'] == '12:34:56'
        assert r.json['txt'] == 'txt'

    # Test: if JSONEncoderEx calls original default() method for unknown types.
    # In such situation exception will be raised (not serializable).
    def test_encoder_invalid(self):
        with pytest.raises(TypeError):
            json_response(fake=object())
