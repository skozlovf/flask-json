import os.path as op
import re
from setuptools import setup


def read(name, only_open=False):
    f = open(op.join(op.dirname(__file__), name))
    return f if only_open else f.read()


ext_version = None
with read('flask_json.py', only_open=True) as f:
    for line in f:
        if line.startswith('__version__'):
            ext_version,  = re.findall(r"__version__\W*=\W*'([^']+)'", line)
            break


setup(
    name='Flask-JSON',
    version=ext_version,
    url='https://github.com/skozlovf/flask-json',
    license='BSD',
    author='Sergey Kozlov',
    author_email='skozlovf@gmail.com',
    description='Better JSON support for Flask',
    long_description=read('README.rst'),
    py_modules=['flask_json'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=['Flask>=0.10'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-cov']
)
