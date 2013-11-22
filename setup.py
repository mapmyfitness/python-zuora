#!/usr/bin/python -tt

setupArgs = {
    'name': 'mmf-zuora',
    'version': '1.0.0.9',
    'author': 'MapMyFitness',
    'author_email': 'brandon.fredericks@mapmyfitness.com',
    'url': 'http://github.com/mapmyfitness/python-zuora',
    'description': 'Zuora client library.',
    'packages': [
        'zuora',
        'zuora.rest_wrapper',
    ],
}

try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup
else:
    import sys
    import subprocess

    class TestRunner(Command):
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            errno = subprocess.call(['py.test'])
            sys.exit(errno)

    setupArgs.update({
        'tests_require': ['pytest'],
        'cmdclass': {'test': TestRunner},
        #'install_requires': ['suds >= 0.4', 'python-requests'], Worrying about getting dependency chain right later
        'zip_safe': False,
    })

setup(**setupArgs)
